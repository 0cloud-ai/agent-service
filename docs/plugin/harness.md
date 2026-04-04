# Harness 插件接口

> 任何引擎只要实现 `HarnessEngine` 接口，就可以作为 harness 插入 teamagent.services。

---

## 概述

Harness 是 agent-service 的执行引擎。它接收用户消息，在后台启动任务（调用 LLM、执行工具），通过文件监听机制将结果异步回传给系统。

引擎不常驻内存。每次用户发消息时实例化，提交任务后返回一个 `SessionWatcher`，由系统（HarnessService）持有并调度监听。

```
用户发消息
  -> 系统实��化引擎，调用 submit(path, message, provider)
  -> 引擎启动后台任务，返回 SessionWatcher（file_path + session_id）
  -> HarnessService 持有 watcher，用 watchdog 监听 watcher.file_path
  -> 文件变更 -> 系统构造 FileChangeEvent -> 调 engine.watch(event)
  -> engine 返回 list[MessageRecord | EventRecord] -> 系统写入 messages.jsonl
  -> 某条 MessageRecord.done == True -> 停止监听
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
- 构造 `FileChangeEvent` 传给引擎

插件不需要自己读文件、追踪偏移量或解析 JSON。

### SessionWatcher（系统预置，纯数据对象）

由 `submit()` 返回，HarnessService 持有和调度。不含业务逻辑。

```python
@dataclass
class SessionWatcher:
    file_path: str             # 要监听的文件路径
    session_id: str            # 引擎分配的 session_id
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

### MessageRecord / EventRecord（系统预置，watch 返回类型）

`watch()` 方法返回的统一结构体。系统自动补充 `id` 和 `created_at` 后写入 messages.jsonl。

```python
@dataclass
class MessageRecord:
    type: str = "message"      # 固定
    role: str = ""             # "assistant"
    content: str = ""
    done: bool = False         # True 表示本轮执行结束，系统停止监听


@dataclass
class EventRecord:
    type: str = "event"        # 固定
    actor: str = ""            # "agent"
    action: str = ""           # "read_file" | "edit_file" | "create_file" | "delete_file" | "run_command"
    target: str = ""           # 文件路径或命令
    detail: str | None = None  # diff 摘要、执行结果等
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

        引擎自己决定 session_id（可以自己生成 UUID，
        也可以由底层工具创建），通过 SessionWatcher 返回给系统。

        Args:
            path: 工作目录路径
            message: 用户消息内容
            provider: 系统注入的 provider 连接信息

        Returns:
            SessionWatcher（file_path + session_id）
        """
        raise NotImplementedError

    def watch(self, event: FileChangeEvent) -> list[MessageRecord | EventRecord] | None:
        """文件变更时由系统（HarnessService）调用。

        将引擎特有的 jsonl 格式转换为统一结构体。
        返回结构体列表，None 表示跳过本次变更。
        当返回的 MessageRecord 中 done=True 时，系统停止监听。
        """
        raise NotImplementedError
```

---

## 统一结构体

`watch()` 返回 `list[MessageRecord | EventRecord]`，使用上方定义的 dataclass。

示例：

```python
# 返回一条 assistant 消息
MessageRecord(role="assistant", content="Hello! How can I help you today?")

# 返回一条 assistant 消息，标记本轮结束
MessageRecord(role="assistant", content="Done.", done=True)

# 返回一个文件读取事件
EventRecord(actor="agent", action="read_file", target="src/main.py")

# 返回一个编辑事件，带 diff 摘要
EventRecord(actor="agent", action="edit_file", target="src/main.py", detail="+28 -3")
```

### 事件 action

| action | 说明 |
|--------|------|
| `read_file` | 读取文件 |
| `edit_file` | 编辑文件，detail 为 diff 摘要 |
| `create_file` | 创建文件 |
| `delete_file` | 删除文件 |
| `run_command` | 执行终端命令，detail 为结果摘要 |

系统会自动补充 `id` 和 `created_at` 字段后序列化写入 messages.jsonl。

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
        return SessionWatcher(file_path=jsonl_path, session_id=sid)

    def watch(self, event):
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                content = line.get("message", {}).get("content", "")
                is_done = line.get("stop_reason") == "end_turn"
                results.append(MessageRecord(role="assistant", content=content, done=is_done))
            elif msg_type == "tool_use":
                results.append(EventRecord(
                    actor="agent",
                    action=line.get("tool", ""),
                    target=line.get("input", {}).get("path", ""),
                ))
        return results or None
```

## 插件示例：claude-agent-sdk

使用 claude-agent-sdk 的 Python API，底层同样写入 `~/.claude/projects/{slug}/{session_id}.jsonl`。

```python
import asyncio
import uuid
from pathlib import Path

from claude_agent_sdk import query, ClaudeAgentOptions


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
                pass  # SDK 自动写入 jsonl

        asyncio.get_event_loop().create_task(_run())

        slug = path.lstrip("/").replace("/", "-")
        jsonl_path = str(Path.home() / ".claude" / "projects" / slug / f"{sid}.jsonl")
        return SessionWatcher(file_path=jsonl_path, session_id=sid)

    def watch(self, event):
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                content = line.get("message", {}).get("content", "")
                is_done = line.get("stop_reason") == "end_turn"
                results.append(MessageRecord(role="assistant", content=content, done=is_done))
            elif msg_type == "tool_use":
                results.append(EventRecord(
                    actor="agent",
                    action=line.get("tool", ""),
                    target=line.get("input", {}).get("path", ""),
                ))
        return results or None
```

---

## 系统侧执行流程（HarnessService）

```
1. 用户 POST /api/v1/workspace/sessions/{session_id}/messages

2. 系统写入用户消息到 messages.jsonl

3. 根据 session.harness 查找对应的 HarnessEngine 插件

4. 实例化引擎，调用 engine.submit(path, message, provider)
   -> 引擎启动后台任务
   -> 返回 SessionWatcher（file_path + session_id）

5. HarnessService 持有 watcher，用 watchdog 监听 watcher.file_path
   （只关注 modified / created）

6. 文件变更时：
   a. 系统计算增量行，构造 FileChangeEvent
   b. 调 engine.watch(event) -> 拿到 list[MessageRecord | EventRecord]
   c. 系统补充 id 和 created_at，写入 messages.jsonl
   d. 如果某条 MessageRecord.done == True -> 停止监听
```

---

## 约定

1. **引擎不常���内存** -- 每次用户发消息时实例化，submit 后系统持有 SessionWatcher 和 engine 引用
2. **submit 必须立即返回** -- 后台任务异步执行，不阻塞 API 响应
3. **SessionWatcher 是纯数据对象** -- 只有 file_path 和 session_id，不含业务逻辑
4. **watch() 在 Engine 上** -- 系统调 engine.watch() 做格式转换，通过 MessageRecord.done 判断完成
5. **watch() 返回 MessageRecord / EventRecord** -- 不是裸 dict，使用系统预置的结构体
6. **插件不写 messages.jsonl** -- 只返回结构体，系统决定写到哪里（session 或 conversation）
7. **插件不读配置文件** -- provider 信息由系统注入
8. **session_id 由引擎决定** -- 通过 SessionWatcher.session_id 返回给系统
