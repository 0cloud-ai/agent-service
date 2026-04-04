def test_list_harness(client):
    r = client.get("/api/v1/workspace/harness")
    assert r.status_code == 200
    data = r.json()
    assert data["default"] == "opencode"
    assert "claude-agent-sdk" in data["engines"]
    assert "opencode" in data["engines"]


def test_get_harness(client):
    r = client.get("/api/v1/workspace/harness/opencode")
    assert r.status_code == 200
    data = r.json()
    assert data["engine"] == "opencode"
    assert "anthropic" in data["apiFormats"]


def test_get_harness_not_found(client):
    r = client.get("/api/v1/workspace/harness/nonexistent")
    assert r.status_code == 404
