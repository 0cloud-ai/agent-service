"""
Tests for workspace_providers_api — /api/v1/workspace/providers
"""


def _create_provider(client, vendor="anthropic", model="claude-sonnet-4-20250514"):
    """Create a provider via the API and return the response JSON."""
    resp = client.post(
        "/api/v1/workspace/providers",
        json={"vendor": vendor, "model": model},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_provider(client):
    """POST /api/v1/workspace/providers creates a provider."""
    data = _create_provider(client)
    assert "id" in data
    assert data["vendor"] == "anthropic"
    assert data["model"] == "claude-sonnet-4-20250514"
    assert data["api_base_url"] == "https://api.anthropic.com"
    assert data["status"] == "unknown"


def test_list_providers(client):
    """After creating a provider it appears in the list."""
    created = _create_provider(client)

    resp = client.get("/api/v1/workspace/providers")
    assert resp.status_code == 200
    ids = [p["id"] for p in resp.json()]
    assert created["id"] in ids


def test_update_provider(client):
    """PUT /api/v1/workspace/providers/{id} updates the provider."""
    created = _create_provider(client)
    provider_id = created["id"]

    resp = client.put(
        f"/api/v1/workspace/providers/{provider_id}",
        json={"model": "claude-opus-4-20250514"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["model"] == "claude-opus-4-20250514"
    assert data["vendor"] == "anthropic"  # unchanged


def test_delete_provider(client):
    """DELETE /api/v1/workspace/providers/{id} removes the provider."""
    created = _create_provider(client)
    provider_id = created["id"]

    resp = client.delete(f"/api/v1/workspace/providers/{provider_id}")
    assert resp.status_code == 204

    # Confirm it's gone
    resp = client.get("/api/v1/workspace/providers")
    ids = [p["id"] for p in resp.json()]
    assert provider_id not in ids


def test_ping_provider(client):
    """POST /api/v1/workspace/providers/{id}/ping returns health info."""
    created = _create_provider(client)
    provider_id = created["id"]

    resp = client.post(f"/api/v1/workspace/providers/{provider_id}/ping")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "healthy"
    assert data["model"] == "claude-sonnet-4-20250514"
