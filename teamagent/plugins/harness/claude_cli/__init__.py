from __future__ import annotations

import os
import subprocess
import uuid
from pathlib import Path

from teamagent.harness.engine import HarnessEngine
from teamagent.harness.types import FileWatcher, ProviderInfo, Record


class ClaudeCLIEngine(HarnessEngine):
    id = "claude-code-cli"
    name = "Claude Code CLI"
    api_formats = ["anthropic"]

    def submit(self, path: str, message: str, provider: ProviderInfo | None = None) -> FileWatcher:
        sid = str(uuid.uuid4())
        env = os.environ.copy()
        if provider:
            env["ANTHROPIC_BASE_URL"] = provider.base_url
            if provider.api_key:
                env["ANTHROPIC_API_KEY"] = provider.api_key
        cmd = ["claude", "-p", "--session-id", sid]
        if provider:
            cmd.extend(["--model", provider.model_id])
        cmd.extend(["--dangerously-skip-permissions", "--max-turns", "1", message])
        subprocess.Popen(
            cmd,
            cwd=path,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        # CLI 使用 cwd 生成 slug，前面带 -
        slug = "-" + path.lstrip("/").replace("/", "-")
        jsonl_path = str(Path.home() / ".claude" / "projects" / slug / f"{sid}.jsonl")
        return FileWatcher(session_id=sid, file_path=jsonl_path)

    def watch(self, event) -> list[Record] | None:
        """event 是 FileChangeEvent，遍历 new_lines 转换。

        CLI jsonl 行格式：
        - type=queue-operation / user / attachment / last-prompt → 跳过
        - type=assistant → message.content 里有 thinking/text block
        - stop_reason=end_turn → done
        """
        results = []
        for line in event.new_lines:
            line_type = line.get("type")
            if line_type != "assistant":
                continue
            message = line.get("message", {})
            content_blocks = message.get("content", [])
            text_parts = []
            for block in content_blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    text_parts.append(block.get("text", ""))
                # thinking block 跳过
            if not text_parts:
                continue
            content = "\n".join(text_parts)
            is_done = message.get("stop_reason") == "end_turn"
            results.append(Record(role="assistant", content=content, done=is_done))
        return results or None
