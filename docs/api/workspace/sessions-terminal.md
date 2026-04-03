# Workspace — Sessions / Terminal API

> 会话内的终端命令执行（Terminal Tab）。在会话所属目录下执行命令，所有操作会记录为系统事件，内联到对话流中。
>
> 所有接口通过 `?path=` query parameter 指定会话所在目录。

---

## 执行命令

### POST /api/v1/workspace/sessions/{session_id}/terminal?path=...

> 在会话所属目录下执行终端命令。输出通过 SSE 流式返回。

```
POST /api/v1/workspace/sessions/550e8400.../terminal?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "command": "git status"
}
```

**响应（流式 SSE）：**

```
Content-Type: text/event-stream

event: stdout
data: {"content": "On branch main\nnothing to commit, working tree clean\n"}

event: exit
data: {"code": 0, "event_id": "evt-005"}
```

**长时间运行的命令：**

```json
{
  "command": "python -m pytest tests/ -v"
}
```

```
event: stdout
data: {"content": "tests/test_refund.py::test_retry_success PASSED\n"}

event: stdout
data: {"content": "tests/test_refund.py::test_retry_exhausted PASSED\n"}

event: stdout
data: {"content": "tests/test_refund.py::test_empty_order PASSED\n"}

event: stdout
data: {"content": "\n3 passed in 1.24s\n"}

event: exit
data: {"code": 0, "event_id": "evt-006"}
```

**命令失败：**

```json
{
  "command": "python -m pytest tests/test_broken.py"
}
```

```
event: stdout
data: {"content": "tests/test_broken.py::test_something FAILED\n"}

event: stderr
data: {"content": "AssertionError: expected 200 got 500\n"}

event: exit
data: {"code": 1, "event_id": "evt-007"}
```

**SSE 事件类型：**

| 事件 | 说明 |
|------|------|
| `stdout` | 标准输出，逐块推送 |
| `stderr` | 标准错误，逐块推送 |
| `exit` | 命令结束，返回退出码和事件 ID |

`event_id` 指向对话流中生成的系统事件：

```
┄ 林远舟 执行了 git status
┄ 林远舟 执行了 python -m pytest tests/ -v ✓ (3 passed)
┄ 林远舟 执行了 python -m pytest tests/test_broken.py ✗ (1 failed)
```

事件的 `detail` 字段自动摘要命令结果（通过/失败/退出码）。

**状态：** 🆕 需新增

---

## 请求参数

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| command | string | 是 | 要执行的终端命令 |
| timeout | int | 否 | 超时秒数，默认 120，最大 600 |

---

## 响应模型

### ExitEvent

| 字段 | 类型 | 说明 |
|------|------|------|
| code | int | 退出码，0 为成功 |
| event_id | string | 对话流中生成的系统事件 ID |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | command 为空 |
| 403 | 无权限 |
| 404 | 会话不存在 |
| 408 | 命令执行超时 |
