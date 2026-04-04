import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from config.loader import load_config
from main import app


@pytest.fixture
def teamagent_dir(tmp_path):
    base = tmp_path / ".teamagent"
    base.mkdir()
    (base / "users").mkdir()
    (base / "conversations").mkdir()
    config = {
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
    (base / "teamagent.json").write_text(json.dumps(config))
    return base


@pytest.fixture
def client(teamagent_dir):
    app.state.base_path = teamagent_dir
    app.state.config = load_config(teamagent_dir / "teamagent.json")
    app.state.jwt_secret = "test-secret"
    # Clear cached services
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
