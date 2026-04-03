# Workspace — Sessions API

> 会话的列表、详情、创建、对话和成员管理。工程面板右侧面板的数据源。
>
> 会话按目录层级存储在文件系统中（见 [目录上下文](../../context/README.md)），API 直接从 `{path}/.teamagent/sessions/` 读取。
>
> 相关子文档：[sessions-files.md](sessions-files.md)、[sessions-terminal.md](sessions-terminal.md)

---

## 概念

会话（Session）存储在对应目录的 `.teamagent/sessions/` 下，每个会话一个子目录：

```
/home/linyuanzhou/payment-gateway/
└── .teamagent/
    └── sessions/
        ├── 550e8400-e29b-41d4-a716-446655440000/
        │   ├── session.json          # 会话元信息
        │   └── messages.jsonl        # 对话记录（追加写入）
        └── aab91f00-d82e-4f5a-b123-abcdef123456/
            ├── session.json
            └── messages.jsonl
```

- 每个目录拥有独立的会话列表，API 通过 `?path=` query parameter 定位到对应目录
- 会话数据直接从文件系统读取，无需数据库
- `session.json` 存储元信息（标题、harness、成员等）
- `messages.jsonl` 按行追加记录对话消息和事件

---

## 会话列表

### GET /api/v1/workspace/sessions

> 扫描 `{path}/.teamagent/sessions/` 目录，列出该层级的所有会话。

```
GET /api/v1/workspace/sessions?path=/home/linyuanzhou/payment-gateway&sort=updated_at&limit=20
```

```json
{
  "path": "/home/linyuanzhou/payment-gateway",
  "sessions": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "title": "重构 PaymentProcessor 的回调逻辑",
      "harness": "claude-agent-sdk",
      "created_at": "2026-03-23T14:30:00Z",
      "updated_at": "2026-03-23T17:45:00Z",
      "message_count": 47
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 12
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| path | string | — | 目标目录路径（必填） |
| cursor | string? | null | 上一页最后一条的 id |
| limit | int (1-100) | 20 | 每页条数 |
| sort | string | updated_at | `updated_at` 或 `created_at` |

实现：读取 `{path}/.teamagent/sessions/*/session.json`，按 sort 字段排序后分页返回。

**状态：** ✅ 已实现（需迁移路径前缀）

---

## 创建会话

### POST /api/v1/workspace/sessions

> 在指定目录下新建会话，创建 `{path}/.teamagent/sessions/{id}/` 目录及初始文件。

```
POST /api/v1/workspace/sessions
```

```json
{
  "path": "/home/linyuanzhou/payment-gateway",
  "title": "添加退款异步重试机制",
  "harness": "opencode"
}
```

**响应：**

```json
{
  "id": "aab91f00-d82e-4f5a-b123-abcdef123456",
  "title": "添加退款异步重试机制",
  "path": "/home/linyuanzhou/payment-gateway",
  "harness": "opencode",
  "members": [],
  "created_at": "2026-03-26T01:17:00Z",
  "updated_at": "2026-03-26T01:17:00Z",
  "message_count": 0
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| path | string | 是 | 目标目录路径 |
| title | string | 否 | 会话标题，不传则从第一条用户消息自动生成 |
| harness | string | 否 | 使用的 harness 引擎 ID，不传则使用 default harness。**session 创建后 harness 不可更改** |
| members | string[] | 否 | 初始成员的 member_id 列表（来自 workspace members），不传则为空 |

实现：
1. 生成 UUID 作为会话 ID
2. 创建 `{path}/.teamagent/sessions/{id}/` 目录
3. 写入 `session.json`（元信息）
4. 创建空的 `messages.jsonl`

**状态：** 🆕 需新增

---

## 会话对话记录

### GET /api/v1/workspace/sessions/{session_id}/messages

> 读取会话的 `messages.jsonl` 文件，返回对话记录。

```
GET /api/v1/workspace/sessions/550e8400.../messages?path=/home/linyuanzhou/payment-gateway&limit=50
```

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "session": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "重构 PaymentProcessor 的回调逻辑",
    "path": "/home/linyuanzhou/payment-gateway",
    "created_at": "2026-03-23T14:30:00Z",
    "updated_at": "2026-03-26T02:14:00Z",
    "message_count": 68
  },
  "messages": [
    {
      "id": "msg-001",
      "type": "message",
      "role": "user",
      "content": "帮我看一下 src/payment_processor.py...",
      "created_at": "2026-03-23T14:30:00Z"
    },
    {
      "id": "msg-002",
      "type": "message",
      "role": "assistant",
      "content": "我来读一下这个文件...",
      "created_at": "2026-03-23T14:30:12Z"
    },
    {
      "id": "evt-001",
      "type": "event",
      "actor": "agent",
      "action": "read_file",
      "target": "src/payment_processor.py",
      "created_at": "2026-03-23T14:30:13Z"
    },
    {
      "id": "evt-002",
      "type": "event",
      "actor": "agent",
      "action": "edit_file",
      "target": "src/payment_processor.py",
      "detail": "+28 -3",
      "created_at": "2026-03-23T14:35:20Z"
    },
    {
      "id": "evt-003",
      "type": "event",
      "actor": "linyuanzhou",
      "action": "edit_file",
      "target": "src/refund_processor.py",
      "detail": "+1 -1",
      "created_at": "2026-03-26T02:10:00Z"
    },
    {
      "id": "evt-004",
      "type": "event",
      "actor": "agent",
      "action": "run_command",
      "target": "python -m pytest tests/test_refund.py",
      "detail": "✓ 3 passed",
      "created_at": "2026-03-26T02:12:00Z"
    }
  ],
  "pagination": {
    "next_cursor": null,
    "has_more": false,
    "total": 68
  }
}
```

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| path | string | — | 目标目录路径（必填） |
| cursor | string? | null | 上一页最后一条的 id |
| limit | int (1-100) | 50 | 每页条数 |
| order | string | asc | `asc`（从头看）或 `desc`（从最新看）|

实现：读取 `{path}/.teamagent/sessions/{session_id}/messages.jsonl`，逐行解析后分页返回。

**消息类型：**

| type | 说明 |
|------|------|
| `message` | 用户或 Agent 的对话消息，有 `role` 和 `content` 字段 |
| `event` | 系统事件（文件操作、命令执行等），有 `actor`、`action`、`target` 字段 |

**事件 actor：** `"agent"` 或用户名（如 `"linyuanzhou"`、`"wangxiao"`）

**事件 action：**

| action | 说明 |
|--------|------|
| `read_file` | 读取文件 |
| `edit_file` | 编辑文件，detail 显示 diff 摘要 |
| `create_file` | 新建文件 |
| `delete_file` | 删除文件 |
| `run_command` | 执行终端命令，detail 显示结果摘要 |
| `member_added` | 成员加入会话，target 为成员名称，detail 为 joined_via |
| `member_removed` | 成员移出会话，target 为成员名称 |

**状态：** 🆕 需新增

---

## 发送消息

### POST /api/v1/workspace/sessions/{session_id}/messages?path=...

> 在会话中发送消息，追加写入 `messages.jsonl`，Agent 流式返回响应。

```
POST /api/v1/workspace/sessions/550e8400.../messages?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "content": "在 RefundProcessor 里加一个异步重试机制，失败后按 1s、2s、4s 的间隔指数退避，最多重试 3 次。"
}
```

**带 @ 提及的消息：**

```json
{
  "content": "@设计团队 活动页面的视觉设计需要多久？",
  "mentions": ["mem-003"]
}
```

被 @ 的成员如果不在当前 session 的 members 中，会**自动加入**。

**引用服务工单：**

```json
{
  "content": "参考 @conv-001 的需求，陈霜要的是支付成功后发 10 元优惠券。",
  "mentions": ["conv-001"]
}
```

`mentions` 统一支持 member（`mem-xxx`）和 conversation（`conv-xxx`），系统根据 ID 自动识别。引用工单时，Agent 可以读取工单的完整上下文来辅助工作。详见 [service-inbox.md](service-inbox.md)。

**响应（流式 SSE）：**

```
Content-Type: text/event-stream

event: thinking
data: {"content": "让我先读取 src/refund_processor.py 的当前内容..."}

event: tool_use
data: {"tool": "read_file", "path": "src/refund_processor.py"}

event: text
data: {"content": "我看到了当前的实现。接下来添加指数退避的重试机制..."}

event: tool_use
data: {"tool": "edit_file", "path": "src/refund_processor.py", "description": "添加异步重试逻辑"}

event: text
data: {"content": "重试机制已添加。跑一遍测试..."}

event: tool_use
data: {"tool": "run_command", "command": "python -m pytest tests/test_refund.py"}

event: text
data: {"content": "所有测试通过 ✓"}

event: done
data: {"message_id": "msg-069", "session_updated_at": "2026-03-26T02:14:00Z"}
```

流式响应的同时，每条消息和事件实时追加到 `messages.jsonl`。

| 事件 | 说明 |
|------|------|
| `thinking` | Agent 的思考过程 |
| `text` | Agent 的文本回复 |
| `tool_use` | Agent 调用工具（读文件、编辑文件、执行命令等）|
| `tool_result` | 工具执行结果 |
| `error` | 错误信息 |
| `done` | 本轮响应结束 |

**状态：** 🆕 需新增

---

## 会话成员

Session 可以有自己的 members，是 workspace members 的子集。成员信息记录在 `session.json` 中。加入方式：

- 创建会话时通过 `members` 字段指定
- 发消息时 @ 提及，被 @ 的成员自动加入
- 手动添加

### GET /api/v1/workspace/sessions/{session_id}/members?path=...

> 读取 `session.json` 中的成员列表。

```
GET /api/v1/workspace/sessions/550e8400.../members?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "members": [
    {
      "id": "mem-001",
      "type": "user",
      "name": "林远舟",
      "joined_at": "2026-03-23T14:30:00Z",
      "joined_via": "creator"
    },
    {
      "id": "mem-003",
      "type": "service",
      "name": "设计团队",
      "service_url": "https://design.agent.team.dev",
      "status": "connected",
      "joined_at": "2026-03-26T09:00:00Z",
      "joined_via": "mention"
    },
    {
      "id": "mem-002",
      "type": "user",
      "name": "小王",
      "joined_at": "2026-03-26T10:00:00Z",
      "joined_via": "manual"
    }
  ]
}
```

`joined_via` 表示成员如何加入本会话：

| joined_via | 说明 |
|------------|------|
| `creator` | 创建会话的人 |
| `mention` | 被 @ 后自动加入 |
| `manual` | 手动添加 |

**状态：** 🆕 需新增

### POST /api/v1/workspace/sessions/{session_id}/members?path=...

> 手动添加成员到会话，更新 `session.json` 并在 `messages.jsonl` 中追加事件。

```
POST /api/v1/workspace/sessions/550e8400.../members?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "member_id": "mem-002"
}
```

**响应：**

```json
{
  "id": "mem-002",
  "type": "user",
  "name": "小王",
  "joined_at": "2026-03-26T10:00:00Z",
  "joined_via": "manual"
}
```

添加成员会在对话流中产生系统事件：

```
┄ 林远舟 添加了 小王 到会话
```

**状态：** 🆕 需新增

### DELETE /api/v1/workspace/sessions/{session_id}/members/{member_id}?path=...

> 从会话中移除成员，更新 `session.json` 并在 `messages.jsonl` 中追加事件。

```
DELETE /api/v1/workspace/sessions/550e8400.../members/mem-003?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "message": "已从会话中移除 设计团队"
}
```

移除成员会在对话流中产生系统事件：

```
┄ 林远舟 移除了 设计团队
```

**状态：** 🆕 需新增

---

## 文件系统存储格式

### session.json

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "title": "重构 PaymentProcessor 的回调逻辑",
  "path": "/home/linyuanzhou/payment-gateway",
  "harness": "claude-agent-sdk",
  "members": [
    {
      "id": "mem-001",
      "type": "user",
      "name": "林远舟",
      "joined_at": "2026-03-23T14:30:00Z",
      "joined_via": "creator"
    }
  ],
  "created_at": "2026-03-23T14:30:00Z",
  "updated_at": "2026-03-23T17:45:00Z",
  "message_count": 47
}
```

### messages.jsonl

每行一条 JSON，追加写入：

```jsonl
{"id":"msg-001","type":"message","role":"user","content":"帮我看一下 src/payment_processor.py...","created_at":"2026-03-23T14:30:00Z"}
{"id":"msg-002","type":"message","role":"assistant","content":"我来读一下这个文件...","created_at":"2026-03-23T14:30:12Z"}
{"id":"evt-001","type":"event","actor":"agent","action":"read_file","target":"src/payment_processor.py","created_at":"2026-03-23T14:30:13Z"}
```

---

## 响应模型

### Session

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话 ID（UUID）|
| title | string | 会话标题 |
| path | string | 所属目录路径 |
| harness | string | 使用的 harness 引擎 ID（创建后不可更改）|
| members | Member[] | 当前会话成员列表 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |
| message_count | int | 消息+事件总数 |

### Message（type = "message"）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 消息 ID |
| type | string | 固定为 `"message"` |
| role | string | `user` 或 `assistant` |
| content | string | 消息内容 |
| created_at | datetime | 发送时间 |

### Event（type = "event"）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 事件 ID |
| type | string | 固定为 `"event"` |
| actor | string | 操作者：`"agent"` 或用户名 |
| action | string | 操作类型：`read_file`、`edit_file`、`create_file`、`delete_file`、`run_command` |
| target | string | 操作目标（文件路径或命令）|
| detail | string? | 操作详情（diff 摘要、执行结果等）|
| created_at | datetime | 发生时间 |

### Pagination

| 字段 | 类型 | 说明 |
|------|------|------|
| next_cursor | string? | 下一页游标 |
| has_more | bool | 是否有下一页 |
| total | int | 总数 |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 参数校验失败 |
| 404 | 路径/会话/文件不存在 |
| 403 | 无权限（非该 agent-service 成员）|

---

## 前端调用流程

```
点击目录
  → GET /api/v1/workspace/sessions?path=/home/.../project
    （扫描 {path}/.teamagent/sessions/ 目录）

点 "Load more"
  → GET /api/v1/workspace/sessions?path=...&cursor=xxx

新建会话（可选指定 harness 和初始 members）
  → POST /api/v1/workspace/sessions
    （body 中带 path，创建 {path}/.teamagent/sessions/{id}/ 目录）

点击会话 → 打开 Chat Tab
  → GET /api/v1/workspace/sessions/{id}/messages?path=...
    （读取 messages.jsonl）

查看/管理会话成员
  → GET /api/v1/workspace/sessions/{id}/members?path=...
  → POST /api/v1/workspace/sessions/{id}/members?path=...    （手动添加）
  → DELETE /api/v1/workspace/sessions/{id}/members/{mid}?path=...（移除）

在 Chat Tab 发消息（@ 提及的成员自动加入会话）
  → POST /api/v1/workspace/sessions/{id}/messages?path=...
  → SSE 流式渲染 Agent 响应（同时追加到 messages.jsonl）

Files Tab / Terminal Tab → 见 sessions-files.md / sessions-terminal.md
```
