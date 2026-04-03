# 目录上下文 — Sessions（会话）

> 每个目录下的 `.teamagent/sessions/` 存储该层级发起的会话记录。会话数据直接存储在文件系统，API 从文件系统读写，无需数据库。

---

## 目录结构

```
{path}/.teamagent/sessions/
├── 550e8400-e29b-41d4-a716-446655440000/
│   ├── session.json            # 会话元信息
│   └── messages.jsonl          # 对话记录（追加写入）
└── aab91f00-d82e-4f5a-b123-abcdef123456/
    ├── session.json
    └── messages.jsonl
```

每个会话一个子目录，以 UUID 命名。

---

## session.json

存储会话的元信息，创建时写入，后续按需更新（如标题变更、成员变动、message_count 递增）。

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

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 会话 ID（UUID） |
| title | string | 会话标题 |
| path | string | 所属目录路径 |
| harness | string | 使用的 harness 引擎 ID（创建后不可更改） |
| members | Member[] | 当前会话成员列表 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |
| message_count | int | 消息+事件总数 |

---

## messages.jsonl

对话记录，每行一条 JSON，追加写入。包含两种类型：`message`（对话消息）和 `event`（系统事件）。

```jsonl
{"id":"msg-001","type":"message","role":"user","content":"帮我看一下 src/payment_processor.py...","created_at":"2026-03-23T14:30:00Z"}
{"id":"msg-002","type":"message","role":"assistant","content":"我来读一下这个文件...","created_at":"2026-03-23T14:30:12Z"}
{"id":"evt-001","type":"event","actor":"agent","action":"read_file","target":"src/payment_processor.py","created_at":"2026-03-23T14:30:13Z"}
{"id":"evt-002","type":"event","actor":"agent","action":"edit_file","target":"src/payment_processor.py","detail":"+28 -3","created_at":"2026-03-23T14:35:20Z"}
```

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
| action | string | 操作类型 |
| target | string | 操作目标（文件路径或命令） |
| detail | string? | 操作详情（diff 摘要、执行结果等） |
| created_at | datetime | 发生时间 |

### 事件 action

| action | 说明 |
|--------|------|
| `read_file` | 读取文件 |
| `edit_file` | 编辑文件，detail 显示 diff 摘要 |
| `create_file` | 新建文件 |
| `delete_file` | 删除文件 |
| `run_command` | 执行终端命令，detail 显示结果摘要 |
| `member_added` | 成员加入会话 |
| `member_removed` | 成员移出会话 |
