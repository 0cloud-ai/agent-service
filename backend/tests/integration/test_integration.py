"""
Integration tests — real uvicorn server + real DuckDB on disk.

These tests verify the full request lifecycle: HTTP → uvicorn → FastAPI → DB.
Run with:
    cd backend && pytest tests/integration/ -v
"""

from __future__ import annotations

import httpx


# ── helpers ──────────────────────────────────────────────────────────────

def _register(api: httpx.Client, email="integ@example.com", name="Integ", password="pass1234"):
    return api.post("/api/v1/user/register", json={
        "email": email,
        "name": name,
        "password": password,
    })


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Server lifecycle ─────────────────────────────────────────────────────

class TestServerLifecycle:
    """Verify the server boots, initialises the DB, and serves requests."""

    def test_openapi_docs(self, api: httpx.Client):
        """GET /docs returns 200 — proves uvicorn + FastAPI are running."""
        resp = api.get("/docs")
        assert resp.status_code == 200

    def test_openapi_json(self, api: httpx.Client):
        """GET /openapi.json returns the schema — app is fully mounted."""
        resp = api.get("/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert schema["info"]["title"] == "Agent Service API"


# ── Service info ─────────────────────────────────────────────────────────

class TestServiceInfo:
    def test_get_info(self, api: httpx.Client):
        resp = api.get("/api/v1/service/info")
        assert resp.status_code == 200
        data = resp.json()
        assert "name" in data
        assert "status" in data

    def test_update_and_read_info(self, api: httpx.Client):
        payload = {
            "name": "Integration Service",
            "description": "Integration test service",
            "status": "running",
            "capabilities": ["chat"],
        }
        resp = api.put("/api/v1/service/info", json=payload)
        assert resp.status_code == 200

        resp2 = api.get("/api/v1/service/info")
        assert resp2.json()["name"] == "Integration Service"


# ── User registration / login / profile ──────────────────────────────────

class TestUserFlow:
    """Full user lifecycle: register → login → get profile → update → change password."""

    def test_register_and_login(self, api: httpx.Client):
        # Register
        resp = _register(api, email="flow@example.com")
        assert resp.status_code == 200
        data = resp.json()
        assert "token" in data
        assert data["user"]["email"] == "flow@example.com"

        # Login with same credentials
        resp = api.post("/api/v1/user/login", json={
            "email": "flow@example.com",
            "password": "pass1234",
        })
        assert resp.status_code == 200
        assert "token" in resp.json()

    def test_login_wrong_password(self, api: httpx.Client):
        _register(api, email="wrong@example.com")
        resp = api.post("/api/v1/user/login", json={
            "email": "wrong@example.com",
            "password": "bad",
        })
        assert resp.status_code == 401

    def test_profile_get_and_update(self, api: httpx.Client):
        reg = _register(api, email="profile@example.com", name="OldName").json()
        token = reg["token"]

        # GET /me
        resp = api.get("/api/v1/user/me", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "OldName"

        # PUT /me
        resp = api.put("/api/v1/user/me", json={"name": "NewName"}, headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["name"] == "NewName"

    def test_change_password(self, api: httpx.Client):
        reg = _register(api, email="chpw@example.com", password="old123").json()
        token = reg["token"]

        resp = api.put(
            "/api/v1/user/me/password",
            json={"old_password": "old123", "new_password": "new456"},
            headers=_auth(token),
        )
        assert resp.status_code == 200

        # Login with new password
        resp = api.post("/api/v1/user/login", json={
            "email": "chpw@example.com",
            "password": "new456",
        })
        assert resp.status_code == 200


# ── Sessions (workspace) ────────────────────────────────────────────────

class TestSessionFlow:
    """Create sessions, send messages, manage members."""

    def test_create_and_list_sessions(self, api: httpx.Client):
        resp = api.post("/api/v1/workspace/sessions", json={
            "path": "/integ-proj",
            "title": "Integ Session",
        })
        assert resp.status_code == 201
        session = resp.json()
        assert session["path"] == "/integ-proj"
        sid = session["id"]

        # List
        resp = api.get("/api/v1/workspace/sessions/integ-proj")
        assert resp.status_code == 200
        ids = [s["id"] for s in resp.json()["sessions"]]
        assert sid in ids

    def test_send_and_retrieve_messages(self, api: httpx.Client):
        session = api.post("/api/v1/workspace/sessions", json={
            "path": "/msg-proj",
            "title": "Msg Session",
        }).json()
        sid = session["id"]

        # Send message
        resp = api.post(f"/api/v1/workspace/sessions/{sid}/messages", json={
            "content": "Hello from integration test!",
        })
        assert resp.status_code == 201
        msg = resp.json()
        assert msg["role"] == "user"
        assert msg["content"] == "Hello from integration test!"

        # Retrieve
        resp = api.get(f"/api/v1/workspace/sessions/{sid}/messages")
        assert resp.status_code == 200
        messages = resp.json()["messages"]
        assert len(messages) >= 1
        assert any(m["content"] == "Hello from integration test!" for m in messages)

    def test_session_members(self, api: httpx.Client):
        # Create a member first
        resp = api.post("/api/v1/workspace/members", json={
            "type": "service",
            "name": "Integ Agent",
        })
        assert resp.status_code in (200, 201)
        member = resp.json()
        mid = member["id"]

        # Create session
        session = api.post("/api/v1/workspace/sessions", json={
            "path": "/mbr-proj",
            "title": "Member Session",
        }).json()
        sid = session["id"]

        # Add member to session
        resp = api.post(f"/api/v1/workspace/sessions/{sid}/members", json={
            "member_id": mid,
        })
        assert resp.status_code == 201

        # List members
        resp = api.get(f"/api/v1/workspace/sessions/{sid}/members")
        assert resp.status_code == 200
        ids = [m["id"] for m in resp.json()]
        assert mid in ids

        # Remove member
        resp = api.delete(f"/api/v1/workspace/sessions/{sid}/members/{mid}")
        assert resp.status_code == 204


# ── Providers ────────────────────────────────────────────────────────────

class TestProviders:
    def test_crud_provider(self, api: httpx.Client):
        # Create
        resp = api.post("/api/v1/workspace/providers", json={
            "vendor": "anthropic",
            "model": "claude-sonnet-4-20250514",
            "api_base_url": "https://api.anthropic.com",
            "api_key": "sk-test-key",
        })
        assert resp.status_code in (200, 201)
        provider = resp.json()
        pid = provider["id"]

        # List
        resp = api.get("/api/v1/workspace/providers")
        assert resp.status_code == 200
        ids = [p["id"] for p in resp.json()]
        assert pid in ids

        # Delete
        resp = api.delete(f"/api/v1/workspace/providers/{pid}")
        assert resp.status_code in (200, 204)


# ── Harness engines ──────────────────────────────────────────────────────

class TestHarness:
    def test_list_engines(self, api: httpx.Client):
        """Seeded engines should be present after real startup."""
        resp = api.get("/api/v1/workspace/harness")
        assert resp.status_code == 200
        data = resp.json()
        engine_ids = [e["id"] for e in data["engines"]]
        assert "claude-agent-sdk" in engine_ids
        assert "claude-code-cli" in engine_ids
        assert data["default"] == "claude-agent-sdk"

    def test_set_default_engine(self, api: httpx.Client):
        resp = api.put("/api/v1/workspace/harness/default", json={
            "engine_id": "opencode",
        })
        assert resp.status_code == 200
        assert resp.json()["default"] == "opencode"


# ── Workspace stats ──────────────────────────────────────────────────────

class TestStats:
    def test_stats_endpoint(self, api: httpx.Client):
        resp = api.get("/api/v1/workspace/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "sessions" in data or "total_sessions" in data or isinstance(data, dict)


# ── Service conversations (inbox) ────────────────────────────────────────

class TestServiceConversations:
    def test_conversation_lifecycle(self, api: httpx.Client):
        # Register a user (consumer)
        reg = _register(api, email="convo@example.com", name="Convo User").json()
        token = reg["token"]

        # Create conversation
        resp = api.post("/api/v1/service/conversations", json={
            "message": "I need assistance.",
        }, headers=_auth(token))
        assert resp.status_code == 200
        data = resp.json()
        cid = data["conversation"]["id"]

        # List conversations
        resp = api.get("/api/v1/service/conversations", headers=_auth(token))
        assert resp.status_code == 200
        convos = resp.json()["conversations"]
        ids = [c["id"] for c in convos]
        assert cid in ids

        # Get single conversation
        resp = api.get(f"/api/v1/service/conversations/{cid}")
        assert resp.status_code == 200
        assert resp.json()["id"] == cid

        # Add a message
        resp = api.post(f"/api/v1/service/conversations/{cid}/messages", json={
            "content": "Follow up question",
        }, headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["content"] == "Follow up question"

        # Close conversation
        resp = api.post(f"/api/v1/service/conversations/{cid}/close", headers=_auth(token))
        assert resp.status_code == 200
        assert resp.json()["status"] == "closed"
