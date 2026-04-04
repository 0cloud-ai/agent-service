import json
import shutil
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from teamagent.config.loader import load_config
from teamagent.app import app


# ---------------------------------------------------------------------------
# 通用 helper: 从场景目录的 teamagent.json 创建 TestClient
# ---------------------------------------------------------------------------

def make_client(config_path: Path, tmp_path: Path) -> TestClient:
    """从指定的 teamagent.json 创建 TestClient。

    config_path: 场景目录下的 teamagent.json 路径
    tmp_path: pytest tmp_path fixture
    """
    base = tmp_path / ".teamagent"
    base.mkdir(exist_ok=True)
    (base / "users").mkdir(exist_ok=True)
    (base / "conversations").mkdir(exist_ok=True)
    shutil.copy(config_path, base / "teamagent.json")

    app.state.base_path = base
    app.state.config = load_config(base / "teamagent.json")
    app.state.jwt_secret = "test-secret-key-32bytes-long!!"
    # Clear cached services
    for attr in list(app.state._state.keys()):
        if attr.startswith("_"):
            try:
                delattr(app.state, attr)
            except KeyError:
                pass
    return TestClient(app)


# ---------------------------------------------------------------------------
# 旧版兼容 fixtures（供未迁移的测试继续使用）
# ---------------------------------------------------------------------------

_DEFAULT_CONFIG = {
    "providers": {
        "claude": {
            "baseUrl": "https://api.anthropic.com",
            "apiKey": "sk-test",
            "apiFormat": "anthropic",
            "models": [
                {"id": "claude-sonnet-4", "name": "Claude Sonnet 4"},
                {"id": "claude-opus-4", "name": "Claude Opus 4"},
            ]
        },
        "openai": {
            "baseUrl": "https://api.openai.com",
            "apiKey": "sk-test",
            "apiFormat": "openai-completions",
            "models": [
                {"id": "gpt-4o", "name": "GPT-4o"},
            ]
        },
    },
    "harnesses": {
        "default": "opencode",
        "engines": {
            "claude-agent-sdk": {
                "engine": "claude-agent-sdk",
                "name": "Claude Agent SDK",
                "description": "Anthropic Agent SDK",
                "apiFormats": ["anthropic"],
            },
            "opencode": {
                "engine": "opencode",
                "name": "OpenCode",
                "description": "Open source code agent",
                "apiFormats": ["openai-completions", "anthropic"],
            },
        }
    },
    "members": [
        {"id": "mem-001", "type": "user", "name": "Alice", "email": "alice@test.com", "role": "owner"},
        {"id": "mem-002", "type": "user", "name": "Bob", "email": "bob@test.com", "role": "member"},
        {"id": "mem-003", "type": "service", "name": "Design Team", "serviceUrl": "https://design.test"},
    ],
}


@pytest.fixture
def teamagent_dir(tmp_path):
    base = tmp_path / ".teamagent"
    base.mkdir()
    (base / "users").mkdir()
    (base / "conversations").mkdir()
    (base / "teamagent.json").write_text(json.dumps(_DEFAULT_CONFIG))
    return base


@pytest.fixture
def client(teamagent_dir):
    app.state.base_path = teamagent_dir
    app.state.config = load_config(teamagent_dir / "teamagent.json")
    app.state.jwt_secret = "test-secret"
    for attr in list(app.state._state.keys()):
        if attr.startswith("_"):
            try:
                delattr(app.state, attr)
            except KeyError:
                pass
    return TestClient(app)


def _register(client, email="alice@test.com", name="Alice", password="pass123"):
    return client.post("/api/v1/user/register", json={
        "email": email, "password": password, "name": name,
    })


def _auth_header(token):
    return {"Authorization": f"Bearer {token}"}
