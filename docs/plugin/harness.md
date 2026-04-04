# Harness 插件接口

> 任何引擎只要实现 `HarnessEngine` 接口，就可以作为 harness 插入 teamagent.services。

---

## 概述

Harness 是 agent-service 的执行引擎。它接收用户消息，在后台启动任务（调用 LLM、执行工具），通过文件监听机制将结果异步回传给系统。

引擎不常驻内存。每次用户发消息时实例化，提交任务后返回一个 `SessionWatcher`，系统通过监听文件变更获取执行结果。

```
用户发消息
  → 系统实例化引擎，调用 submit(path, message, provider)
  → 引擎启动后台任务，返回 SessionWatcher
  → 系统用 watchdog 监听 watcher.file_path
  → 文件变更 → 系统构造 FileChangeEvent → 调 watcher.on_change(event)
  → watcher 返回统一结构体 → 系统写入 messages.jsonl
  → watcher.is_complete(event) 返回 True → 停止监听
```

---

## 接口定义

### FileChangeEvent（系统预置）

文件变更事件，包装 watchdog 的 `FileSystemEvent`，附加增量信息。系统只监听 `modified` 和 `created` 事件。

```python
from dataclasses import dataclass


@dataclass
class FileChangeEvent:
    event_type: str            # "modified" | "created"
    file_path: str             # 变更的文件路径
    new_lines: list[dict]      # 本次新增的行（已 json.loads 解析）
    total_lines: int           # 文件当前总行数
```

系统负责：
- 跟踪文件读取位置，计算增量行
- 解析每行 JSON
- 构造 `FileChangeEvent` 传给 watcher

插件不需要自己读文件、追踪偏移量或解析 JSON。

### SessionWatcher（系统预置基类，插件继承）

```python
class SessionWatcher:
    """监听引擎输出的基类。插件继承并实现三个方法。"""

    def __init__(self, file_path: str):
        self.file_path = file_path     # 要监听的文件路径

    @property
    def session_id(self) -> str:
        """返回该 watcher 关联的 session_id。
        引擎自己决定 session_id（可能自己生成，也可能由底层工具创建）。
        """
        raise NotImplementedError

    def on_change(self, event: FileChangeEvent) -> list[dict] | None:
        """文件变更时系统调用。
        将引擎特有的 jsonl 格式转换为统一结构体。
        返回结构体列表，None 表示跳过本次变更。
        """
        raise NotImplementedError

    def is_complete(self, event: FileChangeEvent) -> bool:
        """判断引擎任务是否执行完成。
        返回 True 后系统停止监听。
        """
        raise NotImplementedError
```

### ProviderInfo（系统预置）

系统注入给引擎的 provider 连接信息。

```python
@dataclass
class ProviderInfo:
    name: str                  # provider 配置名（如 "minmax"）
    base_url: str              # API 地址（已做环境变量插值）
    api_key: str | None        # API 密钥（已做环境变量插值）
    api_format: str            # "anthropic" | "openai-completions" | "ollama"
    model_id: str              # 模型 ID（如 "kimi-k2"）
```

### HarnessEngine（插件实现）

```python
class HarnessEngine:
    """Harness 插件必须实现的接口。"""

    id: str                    # 引擎唯一标识
    name: str                  # 引擎显示名称
    api_formats: list[str]     # 支持的 API 协议格式列表

    def submit(self, path: str, message: str,
               provider: ProviderInfo) -> SessionWatcher:
        """提交任务，启动后台执行，返回 SessionWatcher。

        Args:
            path: 工作目录路径
            message: 用户消息内容
            provider: 系统注入的 provider 连接信息

        Returns:
            SessionWatcher 实例，系统据此监听执行结果
        """
        raise NotImplementedError
```

---

## 统一结构体

`on_change()` 返回的 dict 必须符合以下格式：

### Message（对话消息）

```json
{
  "type": "message",
  "role": "assistant",
  "content": "Hello! How can I help you today?"
}
```

### Event（系统事件）

```json
{
  "type": "event",
  "actor": "agent",
  "action": "read_file",
  "target": "src/main.py",
  "detail": null
}
```

### 事件 action

| action | 说明 |
|--------|------|
| `read_file` | 读取文件 |
| `edit_file` | 编辑文件，detail 为 diff 摘要 |
| `create_file` | 创建文件 |
| `delete_file` | 删除文件 |
| `run_command` | 执行终端命令，detail 为结果摘要 |

系统会自动补充 `id` 和 `created_at` 字段后写入 messages.jsonl。

---

## 插件目录与发现

插件放在 `teamagent/plugins/` 目录下，每个插件一个 Python 文件：

```
teamagent/plugins/
├── __init__.py
├── claude_cli.py          # claude -p CLI 插件
└── claude_sdk.py          # claude-agent-sdk 插件
```

系统启动时扫描该目录，查找所有 `HarnessEngine` 子类并注册。配置中的 `engine` 字段与插件的 `id` 属性匹配。

---

## 插件示例：claude-code-cli

使用 `claude -p` 命令行工具，通过 `--session-id` 指定 session，监听 `~/.claude/projects/{slug}/{session_id}.jsonl`。

```python
import subprocess
import uuid
from pathlib import Path


class ClaudeCLIWatcher(SessionWatcher):
    def __init__(self, file_path: str, sid: str):
        super().__init__(file_path)
        self._session_id = sid

    @property
    def session_id(self) -> str:
        return self._session_id

    def on_change(self, event: FileChangeEvent) -> list[dict] | None:
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                content = line.get("message", {}).get("content", "")
                results.append({"type": "message", "role": "assistant", "content": content})
            elif msg_type == "tool_use":
                results.append({
                    "type": "event",
                    "actor": "agent",
                    "action": line.get("tool", ""),
                    "target": line.get("input", {}).get("path", ""),
                })
        return results or None

    def is_complete(self, event: FileChangeEvent) -> bool:
        for line in event.new_lines:
            if line.get("stop_reason") == "end_turn":
                return True
        return False


class ClaudeCLIEngine(HarnessEngine):
    id = "claude-code-cli"
    name = "Claude Code CLI"
    api_formats = ["anthropic"]

    def submit(self, path, message, provider):
        sid = str(uuid.uuid4())
        subprocess.Popen([
            "claude", "-p",
            "--session-id", sid,
            "--cwd", path,
            "--model", provider.model_id,
            message,
        ])
        slug = path.lstrip("/").replace("/", "-")
        jsonl_path = str(Path.home() / ".claude" / "projects" / slug / f"{sid}.jsonl")
        return ClaudeCLIWatcher(jsonl_path, sid)
```

## 插件示例：claude-agent-sdk

使用 claude-agent-sdk 的 Python API，底层同样写入 `~/.claude/projects/{slug}/{session_id}.jsonl`。

```python
import asyncio
import uuid
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions


class ClaudeSDKWatcher(SessionWatcher):
    def __init__(self, file_path: str, sid: str):
        super().__init__(file_path)
        self._session_id = sid

    @property
    def session_id(self) -> str:
        return self._session_id

    def on_change(self, event: FileChangeEvent) -> list[dict] | None:
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                content = line.get("message", {}).get("content", "")
                results.append({"type": "message", "role": "assistant", "content": content})
            elif msg_type == "tool_use":
                results.append({
                    "type": "event",
                    "actor": "agent",
                    "action": line.get("tool", ""),
                    "target": line.get("input", {}).get("path", ""),
                })
        return results or None

    def is_complete(self, event: FileChangeEvent) -> bool:
        for line in event.new_lines:
            if line.get("stop_reason") == "end_turn":
                return True
        return False


class ClaudeSDKEngine(HarnessEngine):
    id = "claude-agent-sdk"
    name = "Claude Agent SDK"
    api_formats = ["anthropic"]

    def submit(self, path, message, provider):
        sid = str(uuid.uuid4())

        async def _run():
            async for _ in query(
                prompt=message,
                options=ClaudeAgentOptions(
                    cwd=path,
                    model=provider.model_id,
                    session_id=sid,
                ),
            ):
                pass  # SDK 自动写入 jsonl，不需要处理返回

        asyncio.get_event_loop().create_task(_run())

        slug = path.lstrip("/").replace("/", "-")
        jsonl_path = str(Path.home() / ".claude" / "projects" / slug / f"{sid}.jsonl")
        return ClaudeSDKWatcher(jsonl_path, sid)
```

---

## 系统侧执行流程

```
1. 用户 POST /api/v1/workspace/sessions/{session_id}/messages

2. 系统写入用户消息到 messages.jsonl

3. 根据 session.harness 查找对应的 HarnessEngine 插件

4. 实例化引擎，调用 submit(path, message, provider)
   → 引擎启动后台任务
   → 返回 SessionWatcher

5. 系统用 watchdog 监听 watcher.file_path（只关注 modified / created）

6. 文件变更时：
   a. 系统计算增量行，构造 FileChangeEvent
   b. 调 watcher.on_change(event) → 拿到统一结构体列表
   c. 写入 session 的 messages.jsonl（系统负责，插件不关心）
   d. 调 watcher.is_complete(event) → True 则停止监听
```

---

## 约定

1. **引擎不常驻内存** — 每次用户发消息时实例化，submit 后系统只持有 SessionWatcher
2. **submit 必须立即返回** — 后台任务异步执行，不阻塞 API 响应
3. **插件不写 messages.jsonl** — 只返回结构体，系统决定写到哪里（session 或 conversation）
4. **插件不读配置文件** — provider 信息由系统注入
5. **session_id 由引擎决定** — 通过 `watcher.session_id` 返回给系统
6. **两个独立插件** — claude-code-cli 和 claude-agent-sdk 是独立实现，不共享基类
