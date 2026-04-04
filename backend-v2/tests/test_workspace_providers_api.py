def test_list_providers(client):
    r = client.get("/api/v1/workspace/providers")
    assert r.status_code == 200
    data = r.json()
    assert "claude" in data["providers"]
    assert "openai" in data["providers"]
    assert data["providers"]["claude"]["apiFormat"] == "anthropic"
    assert len(data["providers"]["claude"]["models"]) == 2


def test_ping_not_found(client):
    r = client.post("/api/v1/workspace/providers/nonexistent/ping")
    assert r.status_code == 404
