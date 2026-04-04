import json
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock


MOCK_RESPONSE_PATH = Path(__file__).parent / "mock_response.json"


def _make_mock_response():
    data = json.loads(MOCK_RESPONSE_PATH.read_text())
    resp = MagicMock()
    resp.status_code = 200
    resp.json.return_value = data
    return resp


@patch("teamagent.service.provider_service.httpx.AsyncClient")
def test_ping_anthropic_healthy(mock_client_cls, client):
    mock_client = AsyncMock()
    mock_client.post.return_value = _make_mock_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    r = client.post("/api/v1/workspace/providers/minmax/ping")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["provider"] == "minmax"
    assert data["model"] == "kimi-k2"
    assert "latency_ms" in data


@patch("teamagent.service.provider_service.httpx.AsyncClient")
def test_ping_anthropic_response_contains_content(mock_client_cls, client):
    mock_client = AsyncMock()
    mock_client.post.return_value = _make_mock_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    r = client.post("/api/v1/workspace/providers/minmax/ping")
    data = r.json()
    content = data["response"]
    assert isinstance(content, list)
    assert len(content) == 2
    assert content[0]["type"] == "thinking"
    assert content[1]["type"] == "text"
    assert content[1]["text"] == "Hello! How can I help you today?"


@patch("teamagent.service.provider_service.httpx.AsyncClient")
def test_ping_anthropic_sends_correct_request(mock_client_cls, client):
    mock_client = AsyncMock()
    mock_client.post.return_value = _make_mock_response()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_client

    client.post("/api/v1/workspace/providers/minmax/ping")

    mock_client.post.assert_called_once()
    call_args = mock_client.post.call_args
    assert "api.minimaxi.com/anthropic/v1/messages" in call_args[0][0]
    body = call_args[1]["json"]
    assert body["model"] == "kimi-k2"
    assert body["messages"][0]["content"] == "hello"
    headers = call_args[1]["headers"]
    assert headers["x-api-key"] == "sk-test-key"
