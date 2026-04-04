# Harness 插件接口

> 任何引擎只要实现 `HarnessEngine` 接口，就可以作为 harness 插入 teamagent.services。

---

## 概述

Harness 是 agent-service 的执行引擎。它接收用户消息，在后台启动任务（调用 LLM、执行工具），将结果异步回传给系统。

引擎不常驻内存。每次用户发消息时实例化，`submit()` 后返回一个 Watcher，由系统（HarnessService）持有并驱动。系统支持两种 Watcher：

- **FileWatcher** — 监听文件变更，适合 CLI 工具等将输出写入 jsonl 的引擎
- **AsyncWatcher** — 消费 async 迭代器，适合原生支持异步流的 SDK 引擎

两条路径中 HarnessService 都是主控方，插件只负责产出 Record，不负责写入。

```
用户发消息
  -> 系统实例化引擎，调用 submit(path, message, provider)

  路径 A — submit 返回 FileWatcher:
    -> watchdog 监听 watcher.file_path
    -> 文件变更 -> 系统构造 FileChangeEvent -> 调 engine.watch(event)
    -> engine 返回 list[Record] -> 系统写入 messages.jsonl
    -> 某条 Record.done == True -> 停止监听

  路径 B — submit 返回 AsyncWatcher:
    -> 系统启动 async task 消费 watcher.iterator
    -> 每次 yield 原始引擎事件 -> 调 engine.watch(event)
    -> engine 返回 list[Record] -> 系统写入 messages.jsonl
    -> 某条 Record.done == True -> 停止消费
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

### Watcher（系统预置）

`submit()` 返回 `FileWatcher` 或 `AsyncWatcher`，HarnessService 根据类型走不同调度路径。

```python
from collections.abc import AsyncIterator


@dataclass
class FileWatcher:
    """文件监听模式。系统用 watchdog 监听 file_path，变更时调 engine.watch()。"""
    session_id: str            # 引擎分配的 session_id
    file_path: str             # 要监听的文件路径


@dataclass
class AsyncWatcher:
    """异步迭代模式。系统消费 iterator 拿到原始事件，再调 engine.watch() 转换。"""
    session_id: str            # 引擎分配的 session_id
    iterator: AsyncIterator    # yield 原始引擎事件（非 Record）
```

设计要点：
- `submit()` 只构造迭代器，**不消费它**，控制权交给 HarnessService
- 两种 Watcher 中系统都是主控方，区别仅在数据源（文件变更 vs async 迭代器）
- **watch() 是统一的格式转换点**，两条路径都经过 watch() 将引擎特有格式转为 Record

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

### Record（系统预置）

`watch()` 返回的统一结构体。通过 `type` 字段区分消息和事件，与系统内部 Message 模型对齐。系统自动补充 `id` 和 `created_at` 后写入 messages.jsonl。

```python
@dataclass
class Record:
    type: str = "message"        # "message" | "event"
    # type=message
    role: str | None = None      # "assistant"
    content: str | None = None
    done: bool = False           # True 表示本轮执行结束，系统停止监听
    # type=event
    actor: str | None = None     # "agent"
    action: str | None = None    # "read_file" | "edit_file" | "create_file" | "delete_file" | "run_command"
    target: str | None = None    # 文件路径或命令
    detail: str | None = None    # diff 摘要、执行结果等
```

### HarnessEngine（插件实现）

```python
class HarnessEngine:
    """Harness 插件必须实现的接口。"""

    id: str                    # 引擎唯一标识
    name: str                  # 引擎显示名称
    api_formats: list[str]     # 支持的 API 协议格式列表

    def submit(self, path: str, message: str,
               provider: ProviderInfo) -> FileWatcher | AsyncWatcher:
        """提交任务，返回 Watcher。

        返回 FileWatcher 时：引擎启动后台进程写文件，系统用 watchdog 监听，
            变更时调 engine.watch() 转换为 Record。
        返回 AsyncWatcher 时：引擎构造 async 迭代器（不消费），
            系统直接驱动消费，迭代器 yield list[Record]。

        Args:
            path: 工作目录路径
            message: 用户消息内容
            provider: 系统注入的 provider 连接信息
        """
        raise NotImplementedError

    def watch(self, event) -> list[Record] | None:
        """统一的格式转换方法，两种 Watcher 模式都会调用。

        FileWatcher 模式：event 是 FileChangeEvent（文件增量数据）
        AsyncWatcher 模式：event 是迭代器 yield 的原始引擎事件

        将引擎特有格式转换为统一 Record。
        返回 Record 列表，None 表示跳过本次事件。
        当返回的 Record 中 done=True 时，系统停止监听/消费。
        """
        raise NotImplementedError
```

---

## 统一结构体

`watch()` 返回 `list[Record]`，通过 `type` 区分消息和事件。

示例：

```python
# 返回一条 assistant 消息
Record(role="assistant", content="Hello! How can I help you today?")

# 返回一条 assistant 消息，标记本轮结束
Record(role="assistant", content="Done.", done=True)

# 返回一个文件读取事件
Record(type="event", actor="agent", action="read_file", target="src/main.py")

# 返回一个编辑事件，带 diff 摘要
Record(type="event", actor="agent", action="edit_file", target="src/main.py", detail="+28 -3")
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

## 插件示例：claude-code-cli（FileWatcher）

使用 `claude -p` 命令行工具，通过 `--session-id` 指定 session。CLI 进程将输出写入 jsonl 文件，系统通过 FileWatcher 监听文件变更，调 `watch()` 转换为 Record。

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
        return FileWatcher(session_id=sid, file_path=jsonl_path)

    def watch(self, event):
        results = []
        for line in event.new_lines:
            msg_type = line.get("type")
            if msg_type == "assistant":
                content = line.get("message", {}).get("content", "")
                is_done = line.get("stop_reason") == "end_turn"
                results.append(Record(role="assistant", content=content, done=is_done))
            elif msg_type == "tool_use":
                results.append(Record(
                    type="event",
                    actor="agent",
                    action=line.get("tool", ""),
                    target=line.get("input", {}).get("path", ""),
                ))
        return results or None
```

## 插件示例：claude-agent-sdk（AsyncWatcher）

使用 claude-agent-sdk 的 Python API。SDK 原生支持 async iterator，`submit()` 构造迭代器但不消费它，控制权交给 HarnessService。迭代器 yield 原始 SDK 事件，系统同样调 `watch()` 做格式转换。

```python
import uuid

from claude_agent_sdk import query, ClaudeAgentOptions


class ClaudeSDKEngine(HarnessEngine):
    id = "claude-agent-sdk"
    name = "Claude Agent SDK"
    api_formats = ["anthropic"]

    def submit(self, path, message, provider):
        sid = str(uuid.uuid4())

        async def _stream():
            async for event in query(
                prompt=message,
                options=ClaudeAgentOptions(
                    cwd=path,
                    model=provider.model_id,
                    session_id=sid,
                ),
            ):
                yield event  # yield 原始 SDK 事件，不做转换

        return AsyncWatcher(session_id=sid, iterator=_stream())

    def watch(self, event):
        # event 是 SDK 原始事件（dict）
        msg_type = event.get("type")
        if msg_type == "assistant":
            content = event.get("message", {}).get("content", "")
            is_done = event.get("stop_reason") == "end_turn"
            return [Record(role="assistant", content=content, done=is_done)]
        elif msg_type == "tool_use":
            return [Record(
                type="event",
                actor="agent",
                action=event.get("tool", ""),
                target=event.get("input", {}).get("path", ""),
            )]
        return None
```

---

## 系统侧执行流程（HarnessService）

```
1. 用户 POST /api/v1/workspace/sessions/{session_id}/messages

2. 系统写入用户消息到 messages.jsonl

3. 根据 session.harness 查找对应的 HarnessEngine 插件

4. 实例化引擎，调用 engine.submit(path, message, provider)
   -> 返回 FileWatcher 或 AsyncWatcher

5a. FileWatcher 路径：
    -> watchdog 监听 watcher.file_path（只关注 modified / created）
    -> 文件变更时：
       a. 系统计算增量行，构造 FileChangeEvent
       b. 调 engine.watch(event) -> 拿到 list[Record]
       c. 系统补充 id 和 created_at，写入 messages.jsonl
       d. 如果某条 Record.done == True -> 停止监听

5b. AsyncWatcher 路径：
    -> 系统启动 async task 消费 watcher.iterator
    -> 每次 yield：
       a. 拿到原始引擎事件
       b. 调 engine.watch(event) -> 拿到 list[Record]
       c. 系统补充 id 和 created_at，写入 messages.jsonl
       d. 如果某条 Record.done == True -> 停止消费
```

---

## 约定

1. **引擎不常驻内存** -- 每次用户发消息时实例化，submit 后系统持有 Watcher 和 engine 引用
2. **submit 必须立即返回** -- FileWatcher 模式启动后台进程写文件；AsyncWatcher 模式构造迭代器但不消费
3. **系统是主控方** -- 无论哪种 Watcher，HarnessService 都驱动消费循环，插件不自行写入 messages.jsonl
4. **watch() 是统一转换点** -- 两种 Watcher 模式都经过 engine.watch() 将引擎特有格式转为 Record
5. **统一产出 Record** -- 不是裸 dict，使用系统预置的统一结构体，type 区分 message/event
6. **插件不读配置文件** -- provider 信息由系统注入
7. **session_id 由引擎决定** -- 通过 Watcher.session_id 返回给系统
