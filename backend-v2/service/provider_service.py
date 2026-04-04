import time
import httpx


class ProviderService:
    async def ping(self, base_url: str, api_key: str | None, api_format: str, model_id: str | None) -> dict:
        try:
            start = time.monotonic()
            async with httpx.AsyncClient(timeout=30.0) as client:
                if api_format == "openai-completions":
                    headers = {}
                    if api_key:
                        headers["Authorization"] = f"Bearer {api_key}"
                    resp = await client.post(
                        f"{base_url}/v1/chat/completions",
                        headers=headers,
                        json={"model": model_id or "test", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                    )
                elif api_format == "anthropic":
                    headers = {}
                    if api_key:
                        headers["x-api-key"] = api_key
                        headers["anthropic-version"] = "2023-06-01"
                    resp = await client.post(
                        f"{base_url}/v1/messages",
                        headers=headers,
                        json={"model": model_id or "test", "messages": [{"role": "user", "content": "ping"}], "max_tokens": 1},
                    )
                elif api_format == "ollama":
                    resp = await client.post(
                        f"{base_url}/api/generate",
                        json={"model": model_id or "test", "prompt": "ping", "stream": False},
                    )
                else:
                    return {"status": "unhealthy", "error": f"Unknown apiFormat: {api_format}"}
            latency = int((time.monotonic() - start) * 1000)
            if resp.status_code < 400:
                return {"status": "healthy", "latency_ms": latency, "model": model_id, "message": "连通正常"}
            else:
                return {"status": "unhealthy", "error": f"{resp.status_code}: {resp.text[:200]}", "message": "连接失败"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "message": "连接失败"}
