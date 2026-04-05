def test_ping_healthy(client):
    r = client.post(
        "/api/v1/workspace/harness/claude-code-cli/ping",
        json={"provider": "minmax"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["engine"] == "claude-code-cli"
    assert data["provider"] == "minmax"
    assert data["latency_ms"] > 0


def test_ping_has_response(client):
    r = client.post(
        "/api/v1/workspace/harness/claude-code-cli/ping",
        json={"provider": "minmax"},
    )
    data = r.json()
    assert data["response"]
    assert isinstance(data["response"], str)
    assert len(data["response"]) > 0
