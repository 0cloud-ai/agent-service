-- Agent Service — DuckDB schema
-- DuckDB 是统一存储层，各数据源 (Claude Agent SDK, OpenCode, …)
-- 通过各自的 adapter 把会话同步写入这里。

-- ── Users ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS users (
    id          VARCHAR PRIMARY KEY,
    email       VARCHAR NOT NULL UNIQUE,
    name        VARCHAR NOT NULL,
    password    VARCHAR NOT NULL,
    created_at  TIMESTAMP NOT NULL
);

-- ── Members ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS members (
    id          VARCHAR PRIMARY KEY,
    type        VARCHAR NOT NULL,            -- 'user' | 'service'
    name        VARCHAR NOT NULL,
    -- type=user fields
    user_id     VARCHAR,                     -- FK to users.id
    email       VARCHAR,
    role        VARCHAR DEFAULT 'member',    -- 'owner' | 'member'
    -- type=service fields
    service_url VARCHAR,
    status      VARCHAR DEFAULT 'connected', -- 'connected' | 'disconnected'
    --
    joined_at   TIMESTAMP NOT NULL
);

-- ── Providers (LLM 供应商) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS providers (
    id          VARCHAR PRIMARY KEY,
    vendor      VARCHAR NOT NULL,             -- 'anthropic' | 'openai' | ...
    model       VARCHAR NOT NULL,
    api_base_url VARCHAR NOT NULL,
    api_key     VARCHAR,
    status      VARCHAR NOT NULL DEFAULT 'unknown',
    created_at  TIMESTAMP NOT NULL
);

-- ── Harness Engines ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS harness_engines (
    id                  VARCHAR PRIMARY KEY,
    name                VARCHAR NOT NULL,
    description         VARCHAR NOT NULL DEFAULT '',
    supported_vendors   VARCHAR NOT NULL DEFAULT '[]'  -- JSON array
);

CREATE TABLE IF NOT EXISTS harness_bindings (
    engine_id   VARCHAR NOT NULL,
    provider_id VARCHAR NOT NULL,
    role        VARCHAR NOT NULL DEFAULT 'default',  -- 'default'|'reasoning'|'fast'|'local'
    PRIMARY KEY (engine_id, provider_id)
);

CREATE TABLE IF NOT EXISTS harness_config (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL
);

-- ── Sessions ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS sessions (
    id          VARCHAR PRIMARY KEY,
    title       VARCHAR NOT NULL,
    path        VARCHAR NOT NULL,
    source      VARCHAR NOT NULL DEFAULT 'unknown',
    harness     VARCHAR NOT NULL DEFAULT '',
    created_at  TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP NOT NULL
);

-- ── Messages ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS messages (
    id          VARCHAR PRIMARY KEY,
    session_id  VARCHAR NOT NULL,
    type        VARCHAR NOT NULL DEFAULT 'message',  -- 'message' | 'event'
    role        VARCHAR,                              -- 'user' | 'assistant' (type=message)
    content     VARCHAR,                              -- (type=message)
    actor       VARCHAR,                              -- (type=event)
    action      VARCHAR,                              -- (type=event)
    target      VARCHAR,                              -- (type=event)
    detail      VARCHAR,                              -- (type=event)
    created_at  TIMESTAMP NOT NULL
);

-- ── Session Members ──────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS session_members (
    session_id  VARCHAR NOT NULL,
    member_id   VARCHAR NOT NULL,
    joined_via  VARCHAR NOT NULL DEFAULT 'manual',  -- 'creator'|'mention'|'manual'
    joined_at   TIMESTAMP NOT NULL,
    PRIMARY KEY (session_id, member_id)
);

-- ── Conversations (服务工单) ─────────────────────────────────────────
CREATE TABLE IF NOT EXISTS conversations (
    id          VARCHAR PRIMARY KEY,
    title       VARCHAR NOT NULL,
    consumer_id VARCHAR NOT NULL,
    status      VARCHAR NOT NULL DEFAULT 'open',  -- 'open'|'escalated'|'closed'
    labels      VARCHAR NOT NULL DEFAULT '[]',    -- JSON array
    closed_at   TIMESTAMP,
    created_at  TIMESTAMP NOT NULL,
    updated_at  TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_messages (
    id              VARCHAR PRIMARY KEY,
    conversation_id VARCHAR NOT NULL,
    role            VARCHAR NOT NULL,  -- 'user' | 'assistant'
    content         VARCHAR NOT NULL,
    created_at      TIMESTAMP NOT NULL
);

-- ── Conversation <-> Session references ──────────────────────────────
CREATE TABLE IF NOT EXISTS conversation_refs (
    conversation_id VARCHAR NOT NULL,
    session_id      VARCHAR NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    PRIMARY KEY (conversation_id, session_id)
);

-- ── Service Info ─────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS service_info (
    key   VARCHAR PRIMARY KEY,
    value VARCHAR NOT NULL
);

-- ── Indexes ──────────────────────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_sessions_path ON sessions(path);
CREATE INDEX IF NOT EXISTS idx_sessions_source ON sessions(source);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_members_type ON members(type);
CREATE INDEX IF NOT EXISTS idx_members_user_id ON members(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status);
CREATE INDEX IF NOT EXISTS idx_conversations_consumer ON conversations(consumer_id);
CREATE INDEX IF NOT EXISTS idx_conv_messages_conv ON conversation_messages(conversation_id);

-- ── Seed data ────────────────────────────────────────────────────────
INSERT OR IGNORE INTO harness_engines (id, name, description, supported_vendors) VALUES
    ('claude-agent-sdk', 'Claude Agent SDK',  'Anthropic 官方 Agent SDK，支持 tool use 和长时间自主执行', '["anthropic"]'),
    ('claude-code-cli',  'Claude Code CLI',   'Claude Code CLI 模式，贴近本地开发体验',                '["anthropic"]'),
    ('opencode',         'OpenCode',          '开源 code agent 引擎，支持多种大模型供应商',             '["anthropic","openai","deepseek","google","ollama"]'),
    ('openclaw',         'OpenClaw',          '开源多模态 agent 引擎',                               '["anthropic","openai"]');

INSERT OR IGNORE INTO harness_config (key, value) VALUES ('default_engine', 'claude-agent-sdk');
