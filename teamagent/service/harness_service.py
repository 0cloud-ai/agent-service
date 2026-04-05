from __future__ import annotations

import asyncio
import logging
import tempfile
import time
from pathlib import Path

from teamagent.config.models import AppConfig
from teamagent.harness.registry import get_engine, list_engines
from teamagent.harness.runner import HarnessRunner
from teamagent.harness.types import AsyncWatcher, FileWatcher, ProviderInfo, Record

logger = logging.getLogger(__name__)

PING_TIMEOUT = 30  # seconds


class HarnessService:
    def get_compatible_providers(self, harness_id: str, config: AppConfig) -> list[str]:
        engine = get_engine(harness_id)
        if engine is None:
            return []
        compatible = []
        for name, provider in config.providers.items():
            if provider.apiFormat in engine.api_formats:
                compatible.append(name)
        return compatible

    async def ping(self, harness_id: str, provider_name: str | None, config: AppConfig) -> dict:
        """通过引擎实际调用 LLM 验证整条链路是否可用。"""
        engine = get_engine(harness_id)
        if engine is None:
            return {"status": "unhealthy", "engine": harness_id, "error": "engine not found", "message": "引擎未注册"}

        provider_info = None
        if provider_name:
            provider_info = self._resolve_provider_by_name(provider_name, engine, config)
            if provider_info is None:
                return {"status": "unhealthy", "engine": harness_id, "error": f"provider '{provider_name}' not found or incompatible", "message": "provider 不可用"}

        try:
            start = time.monotonic()
            with tempfile.TemporaryDirectory() as tmpdir:
                watcher = await engine.submit(tmpdir, "hello", provider_info)
                records = await asyncio.wait_for(
                    self._consume_watcher(engine, watcher),
                    timeout=PING_TIMEOUT,
                )
            latency = int((time.monotonic() - start) * 1000)

            response = ""
            for r in records:
                if r.type == "message" and r.role == "assistant" and r.content:
                    response = r.content[:200]
                    break

            result = {
                "status": "healthy",
                "latency_ms": latency,
                "engine": harness_id,
                "response": response,
                "message": "连通正常",
            }
            if provider_info:
                result["provider"] = provider_info.name
                result["model"] = provider_info.model_id
            return result
        except asyncio.TimeoutError:
            latency = int((time.monotonic() - start) * 1000)
            result = {
                "status": "unhealthy",
                "latency_ms": latency,
                "engine": harness_id,
                "error": "timeout",
                "message": "连接超时",
            }
            if provider_info:
                result["provider"] = provider_info.name
                result["model"] = provider_info.model_id
            return result
        except Exception as e:
            result = {
                "status": "unhealthy",
                "engine": harness_id,
                "error": str(e),
                "message": "连接失败",
            }
            if provider_info:
                result["provider"] = provider_info.name
                result["model"] = provider_info.model_id
            return result

    @staticmethod
    async def _consume_watcher(engine, watcher: FileWatcher | AsyncWatcher) -> list[Record]:
        """消费 watcher 直到 done，收集所有 records（不写文件）。"""
        all_records: list[Record] = []
        if isinstance(watcher, AsyncWatcher):
            try:
                async for raw_event in watcher.iterator:
                    records = await engine.watch(raw_event)
                    if records is None:
                        continue
                    all_records.extend(records)
                    if any(r.done for r in records):
                        break
            except (RuntimeError, GeneratorExit):
                pass
        elif isinstance(watcher, FileWatcher):
            import json
            file_path = Path(watcher.file_path)
            lines_read = 0
            for _ in range(PING_TIMEOUT * 10):
                if not file_path.exists():
                    await asyncio.sleep(0.1)
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        all_lines = f.readlines()
                except FileNotFoundError:
                    await asyncio.sleep(0.1)
                    continue
                if len(all_lines) <= lines_read:
                    await asyncio.sleep(0.1)
                    continue
                new_lines = []
                for line in all_lines[lines_read:]:
                    line = line.strip()
                    if line:
                        try:
                            new_lines.append(json.loads(line))
                        except json.JSONDecodeError:
                            continue
                lines_read = len(all_lines)
                if new_lines:
                    from teamagent.harness.types import FileChangeEvent
                    event = FileChangeEvent(
                        event_type="modified",
                        file_path=str(file_path),
                        new_lines=new_lines,
                        total_lines=lines_read,
                    )
                    records = await engine.watch(event)
                    if records:
                        all_records.extend(records)
                        if any(r.done for r in records):
                            break
        return all_records

    async def run_harness(
        self,
        harness_id: str,
        provider_name: str | None,
        path: str,
        session_id: str,
        message: str,
        config: AppConfig,
        messages_path: Path,
    ) -> None:
        """触发 harness 引擎执行（后台 async task）。"""
        engine = get_engine(harness_id)
        if engine is None:
            logger.warning("Harness engine '%s' not found in registry", harness_id)
            return

        provider_info = None
        if provider_name:
            provider_info = self._resolve_provider_by_name(provider_name, engine, config)

        watcher = await engine.submit(path, message, provider_info)
        runner = HarnessRunner(messages_path)
        asyncio.create_task(runner.run(engine, watcher))
        logger.info(
            "Harness started: engine=%s, session=%s, watcher_session=%s",
            harness_id, session_id, watcher.session_id,
        )

    def _resolve_provider_by_name(
        self, provider_name: str, engine, config: AppConfig
    ) -> ProviderInfo | None:
        """按名称查找 provider，验证与引擎的兼容性。"""
        provider = config.providers.get(provider_name)
        if provider is None:
            return None
        if provider.apiFormat not in engine.api_formats:
            return None
        if not provider.models:
            return None
        return ProviderInfo(
            name=provider_name,
            base_url=provider.baseUrl,
            api_key=provider.apiKey,
            api_format=provider.apiFormat,
            model_id=provider.models[0].id,
        )
