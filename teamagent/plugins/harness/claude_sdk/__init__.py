from __future__ import annotations

import uuid

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    SystemMessage,
    TextBlock,
    ThinkingBlock,
    ToolUseBlock,
    query,
)

from teamagent.harness.engine import HarnessEngine
from teamagent.harness.types import AsyncWatcher, ProviderInfo, Record


class ClaudeSDKEngine(HarnessEngine):
    id = "claude-agent-sdk"
    name = "Claude Agent SDK"
    api_formats = ["anthropic"]

    async def submit(self, path: str, message: str, provider: ProviderInfo | None = None) -> AsyncWatcher:
        sid = str(uuid.uuid4())

        opts: dict = {
            "cwd": path,
            "permission_mode": "bypassPermissions",
        }
        if provider:
            opts["model"] = provider.model_id
            opts["env"] = {
                "ANTHROPIC_BASE_URL": provider.base_url,
                "ANTHROPIC_API_KEY": provider.api_key or "",
            }

        async def _stream():
            async for event in query(
                prompt=message,
                options=ClaudeAgentOptions(**opts),
            ):
                yield event

        return AsyncWatcher(session_id=sid, iterator=_stream())

    async def watch(self, event) -> list[Record] | None:
        """event 是 SDK yield 的原始对象。"""
        if isinstance(event, SystemMessage):
            return None

        if isinstance(event, AssistantMessage):
            text_parts = []
            tool_records = []
            for block in event.content:
                if isinstance(block, ThinkingBlock):
                    continue
                if isinstance(block, TextBlock):
                    text_parts.append(block.text)
                elif isinstance(block, ToolUseBlock):
                    inp = block.input or {}
                    tool_records.append(Record(
                        type="event",
                        actor="agent",
                        action=block.name,
                        target=inp.get("file_path", inp.get("path", inp.get("command", ""))),
                    ))
            records = []
            if text_parts:
                records.append(Record(role="assistant", content="\n".join(text_parts)))
            records.extend(tool_records)
            return records or None

        if isinstance(event, ResultMessage):
            if event.result:
                return [Record(role="assistant", content=event.result, done=True)]
            return [Record(role="assistant", content="", done=True)]

        return None
