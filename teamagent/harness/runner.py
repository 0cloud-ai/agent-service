from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

from teamagent.harness.engine import HarnessEngine
from teamagent.harness.types import (
    AsyncWatcher,
    FileChangeEvent,
    FileWatcher,
    Record,
)
from teamagent.repository.file_utils import append_jsonl

logger = logging.getLogger(__name__)


class HarnessRunner:
    """编排 harness 引擎执行，驱动 FileWatcher / AsyncWatcher 消费循环。"""

    def __init__(self, session_messages_path: Path):
        self._messages_path = session_messages_path

    async def run(self, engine: HarnessEngine, watcher: FileWatcher | AsyncWatcher) -> None:
        if isinstance(watcher, AsyncWatcher):
            await self._run_async(engine, watcher)
        elif isinstance(watcher, FileWatcher):
            await self._run_file(engine, watcher)

    # ── AsyncWatcher 路径 ─────────────────────────────────────────────

    async def _run_async(self, engine: HarnessEngine, watcher: AsyncWatcher) -> None:
        try:
            async for raw_event in watcher.iterator:
                records = engine.watch(raw_event)
                if records is None:
                    continue
                if self._write_records(records):
                    return
        except (RuntimeError, GeneratorExit):
            # SDK 内部 anyio cancel scope 在迭代器关闭时可能报错，安全忽略
            pass
        except Exception:
            logger.exception("AsyncWatcher error for session %s", watcher.session_id)

    # ── FileWatcher 路径 ──────────────────────────────────────────────

    async def _run_file(self, engine: HarnessEngine, watcher: FileWatcher) -> None:
        file_path = Path(watcher.file_path)
        lines_read = 0

        # 等待文件出现
        for _ in range(300):  # 最多等 5 分钟
            if file_path.exists():
                break
            await asyncio.sleep(1)
        else:
            logger.error("FileWatcher timed out waiting for %s", file_path)
            return

        # 轮询增量
        idle_count = 0
        while idle_count < 600:  # 连续 10 分钟无变更则超时
            new_lines, total = self._read_new_lines(file_path, lines_read)
            if not new_lines:
                idle_count += 1
                await asyncio.sleep(1)
                continue

            idle_count = 0
            lines_read = total
            event = FileChangeEvent(
                event_type="modified",
                file_path=str(file_path),
                new_lines=new_lines,
                total_lines=total,
            )
            records = engine.watch(event)
            if records is None:
                continue
            if self._write_records(records):
                return

        logger.warning("FileWatcher timed out (idle) for session %s", watcher.session_id)

    @staticmethod
    def _read_new_lines(path: Path, offset: int) -> tuple[list[dict], int]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                all_lines = f.readlines()
        except FileNotFoundError:
            return [], offset

        total = len(all_lines)
        if total <= offset:
            return [], total

        new = []
        for line in all_lines[offset:]:
            line = line.strip()
            if line:
                try:
                    new.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return new, total

    # ── Record 写入 ──────────────────────────────────────────────────

    def _write_records(self, records: list[Record]) -> bool:
        """写入 records 到 messages.jsonl，返回 True 表示遇到 done。"""
        done = False
        for record in records:
            msg = {
                "id": f"msg-{uuid.uuid4().hex[:8]}",
                "type": record.type,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            if record.type == "message":
                msg["role"] = record.role
                msg["content"] = record.content
            else:
                msg["actor"] = record.actor
                msg["action"] = record.action
                msg["target"] = record.target
                msg["detail"] = record.detail

            append_jsonl(self._messages_path, msg)

            if record.done:
                done = True
        return done
