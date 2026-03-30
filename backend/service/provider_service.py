"""
Provider Service — LLM provider management, vendor defaults, health checks.
"""

from __future__ import annotations

import logging
import time
import uuid
import datetime as dt

logger = logging.getLogger(__name__)

import httpx

from model.do import Vendor
from model.dto import PingResultDTO, ProviderDTO
from repository import provider_repo

# ── Vendor default API base URLs ─────────────────────────────────────

_VENDOR_DEFAULTS: dict[Vendor, str] = {
    Vendor.ANTHROPIC: "https://api.anthropic.com",
    Vendor.OPENAI: "https://api.openai.com",
    Vendor.DEEPSEEK: "https://api.deepseek.com",
    Vendor.GOOGLE: "https://generativelanguage.googleapis.com",
    Vendor.OLLAMA: "http://localhost:11434",
}


def _to_dto(p: dict) -> ProviderDTO:
    return ProviderDTO(
        id=p["id"],
        vendor=p["vendor"],
        model=p["model"],
        api_base_url=p["api_base_url"],
        status=p["status"],
        used_by=p.get("used_by", []),
        created_at=p["created_at"],
    )


# ── Public API ───────────────────────────────────────────────────────


def list_providers() -> list[ProviderDTO]:
    rows = provider_repo.list_providers()
    return [_to_dto(r) for r in rows]


def create_provider(
    vendor: Vendor,
    model: str,
    api_base_url: str | None = None,
    api_key: str | None = None,
) -> ProviderDTO:
    # Resolve api_base_url: explicit > vendor default > required for custom
    if api_base_url is None:
        if vendor in _VENDOR_DEFAULTS:
            api_base_url = _VENDOR_DEFAULTS[vendor]
        else:
            raise ValueError(
                f"api_base_url is required for vendor '{vendor}'"
            )

    provider_id = str(uuid.uuid4())
    now = dt.datetime.now(dt.timezone.utc).isoformat()

    row = provider_repo.create_provider(
        id=provider_id,
        vendor=vendor,
        model=model,
        api_base_url=api_base_url,
        api_key=api_key,
        status="unknown",
        created_at=now,
    )
    return _to_dto(row)


def update_provider(provider_id: str, **fields) -> ProviderDTO | None:
    row = provider_repo.update_provider(provider_id, **fields)
    if row is None:
        return None
    return _to_dto(row)


def delete_provider(provider_id: str) -> bool:
    # Check if any harness binding references this provider
    bindings = provider_repo.get_bindings_for_provider(provider_id)
    if bindings:
        return False

    return provider_repo.delete_provider(provider_id)


def ping_provider(provider_id: str) -> PingResultDTO:
    provider = provider_repo.get_provider(provider_id)
    if provider is None:
        return PingResultDTO(
            status="unhealthy",
            latency_ms=None,
            model=None,
            message=None,
            error="Provider not found",
        )

    vendor = provider["vendor"]
    model = provider["model"]
    api_base_url = provider["api_base_url"].rstrip("/")
    api_key = provider.get("api_key")

    try:
        t0 = time.monotonic()

        if vendor in (Vendor.OPENAI, Vendor.DEEPSEEK):
            resp = httpx.post(
                f"{api_base_url}/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": model,
                    "max_tokens": 32,
                    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                },
                timeout=30,
            )
        elif vendor == Vendor.ANTHROPIC:
            resp = httpx.post(
                f"{api_base_url}/v1/messages",
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key or "",
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model": model,
                    "max_tokens": 256,
                    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                },
                timeout=30,
            )
        elif vendor == Vendor.GOOGLE:
            resp = httpx.post(
                f"{api_base_url}/v1beta/models/{model}:generateContent",
                params={"key": api_key} if api_key else {},
                headers={"Content-Type": "application/json"},
                json={
                    "contents": [{"parts": [{"text": "Say hello in one sentence."}]}],
                    "generationConfig": {"maxOutputTokens": 32},
                },
                timeout=30,
            )
        elif vendor == Vendor.OLLAMA:
            resp = httpx.post(
                f"{api_base_url}/api/chat",
                headers={"Content-Type": "application/json"},
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                    "stream": False,
                },
                timeout=60,
            )
        else:
            # Fallback: try OpenAI-compatible format
            headers = {"Content-Type": "application/json"}
            if api_key:
                headers["Authorization"] = f"Bearer {api_key}"
            resp = httpx.post(
                f"{api_base_url}/v1/chat/completions",
                headers=headers,
                json={
                    "model": model,
                    "max_tokens": 32,
                    "messages": [{"role": "user", "content": "Say hello in one sentence."}],
                },
                timeout=30,
            )

        latency_ms = int((time.monotonic() - t0) * 1000)

        if resp.status_code >= 400:
            provider_repo.update_provider(provider_id, status="unhealthy")
            return PingResultDTO(
                status="unhealthy",
                latency_ms=latency_ms,
                model=model,
                message=None,
                error=f"HTTP {resp.status_code}: {resp.text[:200]}",
            )

        # Extract reply text from response
        body = resp.json()
        print(f"[PING] response body: {body}", flush=True)
        if vendor == Vendor.ANTHROPIC:
            message = next(
                (block.get("text", "") for block in body.get("content", []) if block.get("type") == "text"),
                "",
            )
        elif vendor == Vendor.GOOGLE:
            candidates = body.get("candidates", [{}])
            message = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "") if candidates else ""
        elif vendor == Vendor.OLLAMA:
            message = body.get("message", {}).get("content", "")
        else:
            choices = body.get("choices", [{}])
            message = choices[0].get("message", {}).get("content", "") if choices else ""

        provider_repo.update_provider(provider_id, status="healthy")
        return PingResultDTO(
            status="healthy",
            latency_ms=latency_ms,
            model=model,
            message=message,
            error=None,
        )

    except httpx.TimeoutException:
        provider_repo.update_provider(provider_id, status="unhealthy")
        return PingResultDTO(
            status="unhealthy",
            latency_ms=None,
            model=model,
            message=None,
            error="Request timed out",
        )
    except Exception as e:
        provider_repo.update_provider(provider_id, status="unhealthy")
        return PingResultDTO(
            status="unhealthy",
            latency_ms=None,
            model=model,
            message=None,
            error=str(e),
        )
