def test_empty_providers_returns_empty(client):
    r = client.get("/api/v1/workspace/providers")
    assert r.status_code == 200
    assert r.json()["providers"] == {}
