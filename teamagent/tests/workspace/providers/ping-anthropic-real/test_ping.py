def test_ping_real_healthy(client):
    r = client.post("/api/v1/workspace/providers/minmax/ping")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    assert data["provider"] == "minmax"
    assert data["model"] == "MiniMax-M2.7-highspeed"
    assert data["latency_ms"] > 0


def test_ping_real_has_response(client):
    r = client.post("/api/v1/workspace/providers/minmax/ping")
    data = r.json()
    content = data["response"]
    assert isinstance(content, list)
    assert len(content) > 0
    assert any(block.get("type") == "text" for block in content)
