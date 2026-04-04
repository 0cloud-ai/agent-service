# backend-v2 设计文档

> 基于 docs/ 接口规范，使用 Python + FastAPI 全量实现 backend-v2。配置驱动、文件系统存储、无数据库。

---

## 1. 技术选型

| 项目 | 选择 |
|------|------|
| 语言 | Python 3.12+ |
| 框架 | FastAPI + Uvicorn |
| 存储 | 文件系统（.teamagent/ 目录） |
| 配置 | .teamagent/teamagent.json |
| HTTP 客户端 | httpx（provider/member ping） |
| 测试 | pytest + TestClient |

不使用数据库。所有运行时数据存储在文件系统中。

---

## 2. 项目结构

```
backend-v2/
├── main.py                           # FastAPI app, 路由注册, 启动配置加载
├── requirements.txt
├── .gitignore
│
├── config/
│   ├── loader.py                     # 读取 teamagent.json, ${ENV} 插值
│   └── models.py                     # 配置 Pydantic models
│
├── model/
│   ├── user.py                       # User 相关 models
│   ├── session.py                    # Session, Message, Event models
│   ├── conversation.py               # Conversation models
│   └── member.py                     # Member models
│
├── api/
│   ├── deps.py                       # 共享依赖 (get_config, get_base_path, get_current_user)
│   ├── user_api.py                   # /api/v1/user/*
│   ├── service_info_api.py           # /api/v1/service/info
│   ├── service_conversations_api.py  # /api/v1/service/conversations/*
│   ├── workspace_providers_api.py    # /api/v1/workspace/providers
│   ├── workspace_harness_api.py      # /api/v1/workspace/harness
│   ├── workspace_members_api.py      # /api/v1/workspace/members
│   ├── workspace_sessions_api.py     # /api/v1/workspace/sessions/*
│   ├── workspace_files_api.py        # /api/v1/workspace/sessions/{id}/files/*
│   ├── workspace_terminal_api.py     # /api/v1/workspace/sessions/{id}/terminal
│   ├── workspace_conversations_api.py# /api/v1/workspace/conversations/*
│   └── workspace_stats_api.py        # /api/v1/workspace/stats
│
├── service/
│   ├── user_service.py               # 注册, 登录, token, 密码 hash
│   ├── provider_service.py           # provider 连通性测试 (ping)
│   ├── harness_service.py            # apiFormat 匹配校验, 可用 provider 查询
│   ├── session_service.py            # 会话 CRUD, 消息, mentions 处理
│   ├── conversation_service.py       # 工单 CRUD, 状态流转
│   └── member_service.py             # member 查询, service 成员连通性测试
│
├── repository/
│   ├── file_utils.py                 # atomic_write, append_jsonl, read_jsonl, ensure_dir
│   ├── user_repo.py                  # .teamagent/users/
│   ├── session_repo.py               # {path}/.teamagent/sessions/
│   └── conversation_repo.py          # .teamagent/conversations/
│
└── tests/
    ├── conftest.py                   # fixtures: 临时 .teamagent 目录, TestClient
    ├── test_config_loader.py
    ├── test_user_api.py
    ├── test_workspace_providers_api.py
    ├── test_workspace_harness_api.py
    ├── test_workspace_members_api.py
    ├── test_workspace_sessions_api.py
    ├── test_workspace_files_api.py
    ├── test_workspace_terminal_api.py
    ├── test_workspace_conversations_api.py
    ├── test_service_conversations_api.py
    └── test_service_info_api.py
```

---

## 3. 配置加载

### config/models.py

```python
class ModelConfig(BaseModel):
    id: str
    name: str

class ProviderConfig(BaseModel):
    baseUrl: str
    apiKey: str | None = None
    apiFormat: str            # "openai-completions" | "anthropic" | "ollama"
    models: list[ModelConfig]

class EngineConfig(BaseModel):
    engine: str
    name: str | None = None
    description: str | None = None
    apiFormats: list[str]

class HarnessesConfig(BaseModel):
    default: str | None = None
    engines: dict[str, EngineConfig]

class MemberConfig(BaseModel):
    id: str
    type: str                 # "user" | "service"
    name: str
    email: str | None = None
    role: str | None = None
    serviceUrl: str | None = None

class AppConfig(BaseModel):
    providers: dict[str, ProviderConfig]
    harnesses: HarnessesConfig
    members: list[MemberConfig]
```

### config/loader.py

- `load_config(path: Path) -> AppConfig`
- 读取 JSON 文件，用正则 `\$\{(\w+)\}` 匹配环境变量并替换
- 解析成 AppConfig，校验失败抛异常阻止启动
- 启动时调用一次，存入 `app.state.config`

---

## 4. 数据存储

所有运行时数据通过 repository 层读写文件系统。

### repository/file_utils.py

| 函数 | 说明 |
|------|------|
| `atomic_write(path, data)` | 先写 .tmp 再 rename，防损坏 |
| `append_jsonl(path, obj)` | 追加一行 JSON 到 .jsonl |
| `read_jsonl(path)` | 逐行读取 .jsonl 返回列表 |
| `ensure_dir(path)` | 确保目录存在 |

### repository/user_repo.py

操作 `.teamagent/users/*.json`。

| 方法 | 说明 |
|------|------|
| `list_users()` | 扫描所有 user json |
| `get_user_by_id(id)` | 读取 `user-{id}.json` |
| `get_user_by_email(email)` | 扫描匹配 email |
| `create_user(user)` | atomic_write 新文件 |
| `update_user(id, data)` | 读取、合并、atomic_write |

### repository/session_repo.py

操作 `{path}/.teamagent/sessions/{id}/`，每个 session 包含 `session.json` + `messages.jsonl`。

| 方法 | 说明 |
|------|------|
| `list_sessions(path, sort, limit, cursor)` | 扫描 `*/session.json`，排序分页 |
| `get_session(path, session_id)` | 读取 session.json |
| `create_session(path, session)` | 创建目录 + session.json + 空 messages.jsonl |
| `update_session(path, session_id, data)` | 更新 session.json |
| `list_messages(path, session_id, limit, cursor, order)` | 读取 messages.jsonl 分页 |
| `append_message(path, session_id, message)` | append_jsonl |

### repository/conversation_repo.py

操作 `.teamagent/conversations/{id}/`，结构同 session（`conversation.json` + `messages.jsonl`）。

| 方法 | 说明 |
|------|------|
| `list_conversations(status, label, limit, cursor)` | 扫描过滤分页 |
| `get_conversation(id)` | 读取 conversation.json |
| `create_conversation(conv)` | 创建目录 + conversation.json + 空 messages.jsonl |
| `update_conversation(id, data)` | 更新 conversation.json |
| `list_messages(id, limit, cursor, order)` | 读取 messages.jsonl 分页 |
| `append_message(id, message)` | append_jsonl |

所有 repo 通过构造函数接收 `base_path`（`.teamagent` 根目录），方便测试时指向临时目录。

---

## 5. Service 层

### user_service.py

| 方法 | 说明 |
|------|------|
| `register(email, password, name)` | 生成 salt + sha256 hash，写 user 文件，签发 token |
| `login(email, password)` | 查找 user，验证 hash，签发 token |
| `verify_token(token)` | 解码 JWT，检查过期，返回 user |
| `update_profile(user_id, data)` | 更新 user 文件 |
| `change_password(user_id, old, new)` | 验证旧密码，生成新 salt + hash |

### provider_service.py

| 方法 | 说明 |
|------|------|
| `ping(provider_name, model_id, config)` | 根据 apiFormat 构造 HTTP 请求，测量延迟 |

ping 请求格式：
- `openai-completions` → POST `{baseUrl}/v1/chat/completions`
- `anthropic` → POST `{baseUrl}/v1/messages`
- `ollama` → POST `{baseUrl}/api/generate`

### harness_service.py

| 方法 | 说明 |
|------|------|
| `get_compatible_providers(harness_id, config)` | 遍历 providers，筛选 apiFormat 匹配的 |
| `validate_binding(harness_id, provider_name, config)` | 校验 provider 的 apiFormat 在 harness 的 apiFormats 中 |

### session_service.py

| 方法 | 说明 |
|------|------|
| `create_session(path, title, harness, members)` | 校验 harness，生成 UUID，写文件 |
| `send_message(path, session_id, content, mentions)` | 追加 message，处理 mentions，更新元信息 |
| `add_member(path, session_id, member_id)` | 更新 session.json，追加 member_added 事件 |
| `remove_member(path, session_id, member_id)` | 更新 session.json，追加 member_removed 事件 |

mentions 处理：
- `mem-xxx` → 检查是否已在 session members 中，不在则自动添加
- `conv-xxx` → 记录交叉引用（在 conversation 侧可查到 referenced_by）

### conversation_service.py

| 方法 | 说明 |
|------|------|
| `create_conversation(user_id, message, labels)` | 创建工单，写第一条消息 |
| `send_message(conv_id, content, user_id)` | 追加消息，closed 自动 reopen |
| `escalate(conv_id, reason)` | 状态 → escalated |
| `close(conv_id)` | 状态 → closed |
| `reopen(conv_id)` | 状态 → open |
| `update_labels(conv_id, labels)` | 更新标签 |

### member_service.py

| 方法 | 说明 |
|------|------|
| `list_members(config, type_filter)` | 从 config 读取，按 type 过滤 |
| `ping(member_config)` | HTTP GET serviceUrl/api/v1/service/info，返回延迟 |

---

## 6. API 层

### 调用关系

| API 文件 | 数据来源 | 调用链 |
|---------|---------|--------|
| workspace_providers_api.py | config + HTTP | api → config / provider_service |
| workspace_harness_api.py | config | api → config / harness_service |
| workspace_members_api.py | config + HTTP | api → member_service |
| user_api.py | 文件系统 | api → user_service → user_repo |
| workspace_sessions_api.py | 文件系统 | api → session_service → session_repo |
| workspace_files_api.py | 文件系统 | api → 直接读写文件 |
| workspace_terminal_api.py | 子进程 | api → asyncio.create_subprocess_exec |
| service_conversations_api.py | 文件系统 | api → conversation_service → conversation_repo |
| workspace_conversations_api.py | 文件系统 | api → conversation_service → conversation_repo |
| workspace_stats_api.py | 文件系统 | api → 直接扫描目录 |
| service_info_api.py | config | api → config |

### 共享依赖 (api/deps.py)

```python
def get_config(request: Request) -> AppConfig:
    return request.app.state.config

def get_base_path(request: Request) -> Path:
    return request.app.state.base_path

def get_current_user(request: Request) -> User:
    # Authorization: Bearer <token> → 解析 → 返回 user
    # 失败 → 401
```

### 发消息接口

同步返回。不做 SSE 流式响应，不调用 LLM。发消息追加到 messages.jsonl 后直接返回消息对象。

### sessions 相关接口的 path 参数

所有 session 相关接口通过 `?path=` query parameter 传递目录路径（不放 URL 路径中，避免与路由保留词冲突）。

---

## 7. 测试策略

### conftest.py

```python
@pytest.fixture
def teamagent_dir(tmp_path):
    """临时 .teamagent 目录，含测试用 teamagent.json"""
    base = tmp_path / ".teamagent"
    base.mkdir()
    (base / "users").mkdir()
    (base / "conversations").mkdir()
    # 写入测试配置
    config = { "providers": {...}, "harnesses": {...}, "members": [...] }
    (base / "teamagent.json").write_text(json.dumps(config))
    return base

@pytest.fixture
def client(teamagent_dir):
    app.state.base_path = teamagent_dir
    app.state.config = load_config(teamagent_dir / "teamagent.json")
    return TestClient(app)
```

### 测试文件与覆盖场景

| 测试文件 | 核心场景 |
|---------|---------|
| test_config_loader.py | 环境变量插值、缺失变量报错、配置校验 |
| test_user_api.py | 注册、重复注册 409、登录、错误密码 401、/me、改密码 |
| test_workspace_providers_api.py | 列表返回配置、ping（mock httpx） |
| test_workspace_harness_api.py | 列表、单个详情、apiFormats 正确 |
| test_workspace_members_api.py | 列表、type 过滤、ping（mock httpx） |
| test_workspace_sessions_api.py | 创建、列表、发消息、mentions 自动加成员、成员管理 |
| test_workspace_files_api.py | 目录浏览、读文件、编辑、创建、删除、越权 400 |
| test_workspace_terminal_api.py | 执行命令、超时、退出码 |
| test_workspace_conversations_api.py | 列表、详情、escalate/close/reopen |
| test_service_conversations_api.py | 创建工单、发消息、closed 后发消息 reopen |
| test_service_info_api.py | GET 返回配置信息 |

### Mock 策略

- provider/member ping → mock httpx.AsyncClient
- terminal 执行 → mock asyncio.create_subprocess_exec
- 文件系统 → 真实操作 tmp_path，不 mock

---

## 8. 依赖

```
fastapi>=0.115.0
uvicorn>=0.34.0
httpx>=0.27.0
pyjwt>=2.8.0
pytest>=8.0.0
```

不再需要 DuckDB 和 claude-agent-sdk。
