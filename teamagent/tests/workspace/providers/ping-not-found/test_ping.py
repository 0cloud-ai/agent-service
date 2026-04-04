def test_ping_nonexistent_provider_returns_404(client):
    r = client.post("/api/v1/workspace/providers/nonexistent/ping")
    assert r.status_code == 404


def test_ping_existing_provider_has_model(client):
    """ping 存在的 provider 但不传 model，应自动选第一个。"""
    # 这里不会真正连通，但能验证不会 500
    r = client.post("/api/v1/workspace/providers/claude/ping")
    # 连不通返回 unhealthy 也行，关键是不 500
    assert r.status_code == 200
    data = r.json()
    assert data["provider"] == "claude"
    assert data["model"] == "claude-sonnet-4"
