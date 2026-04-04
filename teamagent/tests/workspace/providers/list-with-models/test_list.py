def test_list_returns_all_providers(client):
    r = client.get("/api/v1/workspace/providers")
    assert r.status_code == 200
    data = r.json()
    assert "claude" in data["providers"]
    assert "openai" in data["providers"]


def test_provider_has_correct_format(client):
    r = client.get("/api/v1/workspace/providers")
    claude = r.json()["providers"]["claude"]
    assert claude["apiFormat"] == "anthropic"
    assert claude["baseUrl"] == "https://api.anthropic.com"


def test_provider_models(client):
    r = client.get("/api/v1/workspace/providers")
    claude = r.json()["providers"]["claude"]
    assert len(claude["models"]) == 2
    assert claude["models"][0]["id"] == "claude-sonnet-4"

    openai = r.json()["providers"]["openai"]
    assert len(openai["models"]) == 1
    assert openai["models"][0]["id"] == "gpt-4o"
