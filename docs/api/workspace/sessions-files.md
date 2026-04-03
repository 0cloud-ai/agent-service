# Workspace — Sessions / Files API

> 会话内的文件浏览和编辑（Files Tab）。操作范围限定在会话所属目录内，所有写操作会记录为系统事件，内联到对话流中。
>
> 所有接口通过 `?path=` query parameter 指定会话所在目录。

---

## 浏览目录

### GET /api/v1/workspace/sessions/{session_id}/files/

> 列出会话所属目录下的文件和子目录。

```
GET /api/v1/workspace/sessions/550e8400.../files/?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "path": "/",
  "entries": [
    { "name": "src", "type": "directory" },
    { "name": "tests", "type": "directory" },
    { "name": "README.md", "type": "file", "size": 2048, "modified_at": "2026-03-25T10:00:00Z" },
    { "name": "requirements.txt", "type": "file", "size": 156, "modified_at": "2026-03-20T08:00:00Z" }
  ]
}
```

**浏览子目录：**

```
GET /api/v1/workspace/sessions/550e8400.../files/src/?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "path": "src/",
  "entries": [
    { "name": "payment_processor.py", "type": "file", "size": 8932, "modified_at": "2026-03-23T14:35:20Z" },
    { "name": "refund_processor.py", "type": "file", "size": 3450, "modified_at": "2026-03-26T02:10:00Z" },
    { "name": "callback_handler.py", "type": "file", "size": 4210, "modified_at": "2026-03-21T16:20:00Z" }
  ]
}
```

**状态：** 🆕 需新增

---

## 读取文件

### GET /api/v1/workspace/sessions/{session_id}/files/{file_path}

> 读取指定文件的内容。

```
GET /api/v1/workspace/sessions/550e8400.../files/src/refund_processor.py?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "path": "src/refund_processor.py",
  "type": "file",
  "size": 3450,
  "modified_at": "2026-03-26T02:10:00Z",
  "content": "class RefundProcessor:\n    ..."
}
```

**状态：** 🆕 需新增

---

## 编辑文件

### PUT /api/v1/workspace/sessions/{session_id}/files/{file_path}

> 用户通过 Files Tab 直接编辑文件。操作会在会话对话流中生成系统事件。

```
PUT /api/v1/workspace/sessions/550e8400.../files/src/refund_processor.py?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "content": "class RefundProcessor:\n    # updated content..."
}
```

**响应：**

```json
{
  "path": "src/refund_processor.py",
  "size": 3450,
  "modified_at": "2026-03-26T02:10:00Z",
  "event_id": "evt-003"
}
```

`event_id` 指向对话流中生成的系统事件：

```
┄ 林远舟 编辑了 src/refund_processor.py (+1 -1)
```

**状态：** 🆕 需新增

---

## 创建文件

### POST /api/v1/workspace/sessions/{session_id}/files/{file_path}

> 在会话所属目录下创建新文件。

```
POST /api/v1/workspace/sessions/550e8400.../files/src/retry_utils.py?path=/home/linyuanzhou/payment-gateway
```

```json
{
  "content": "def retry_with_backoff(func, max_retries=3):\n    ..."
}
```

**响应：**

```json
{
  "path": "src/retry_utils.py",
  "size": 256,
  "modified_at": "2026-03-26T02:11:00Z",
  "event_id": "evt-004"
}
```

**状态：** 🆕 需新增

---

## 删除文件

### DELETE /api/v1/workspace/sessions/{session_id}/files/{file_path}

> 删除指定文件。

```
DELETE /api/v1/workspace/sessions/550e8400.../files/src/old_handler.py?path=/home/linyuanzhou/payment-gateway
```

**响应：**

```json
{
  "path": "src/old_handler.py",
  "event_id": "evt-005"
}
```

**状态：** 🆕 需新增

---

## 响应模型

### DirectoryListing

| 字段 | 类型 | 说明 |
|------|------|------|
| path | string | 当前目录路径 |
| entries | FileEntry[] | 文件和子目录列表 |

### FileEntry

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 文件/目录名 |
| type | string | `file` 或 `directory` |
| size | int? | 文件大小（字节），目录无此字段 |
| modified_at | datetime? | 最后修改时间，目录无此字段 |

### FileContent

| 字段 | 类型 | 说明 |
|------|------|------|
| path | string | 文件路径 |
| type | string | 固定为 `file` |
| size | int | 文件大小（字节）|
| modified_at | datetime | 最后修改时间 |
| content | string | 文件内容 |

### FileWriteResult

| 字段 | 类型 | 说明 |
|------|------|------|
| path | string | 文件路径 |
| size | int | 写入后的文件大小 |
| modified_at | datetime | 修改时间 |
| event_id | string | 对话流中生成的系统事件 ID |

---

## 错误响应

| 状态码 | 说明 |
|--------|------|
| 400 | 路径非法（如试图越权访问会话目录之外）|
| 403 | 无权限 |
| 404 | 会话或文件不存在 |
| 409 | 文件已存在（POST 创建时）|
