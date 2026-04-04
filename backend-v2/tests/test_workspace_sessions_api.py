import os
from tests.conftest import _register, _auth_header


def _create_session(client, path, title="Test Session", harness="opencode"):
    return client.post("/api/v1/workspace/sessions", json={
        "path": path, "title": title, "harness": harness,
    })


def test_create_session(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    r = _create_session(client, path)
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "Test Session"
    assert data["harness"] == "opencode"


def test_create_session_invalid_harness(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    r = _create_session(client, path, harness="nonexistent")
    assert r.status_code == 400


def test_list_sessions(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    _create_session(client, path, title="S1")
    _create_session(client, path, title="S2")
    r = client.get(f"/api/v1/workspace/sessions?path={path}")
    assert r.status_code == 200
    data = r.json()
    assert len(data["sessions"]) == 2
    assert data["pagination"]["total"] == 2


def test_send_and_get_messages(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    sid = _create_session(client, path).json()["id"]
    client.post(f"/api/v1/workspace/sessions/{sid}/messages?path={path}", json={"content": "hello"})
    r = client.get(f"/api/v1/workspace/sessions/{sid}/messages?path={path}")
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 1
    assert r.json()["messages"][0]["content"] == "hello"


def test_mentions_auto_add_member(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    sid = _create_session(client, path).json()["id"]
    client.post(f"/api/v1/workspace/sessions/{sid}/messages?path={path}", json={
        "content": "hey @mem-001", "mentions": ["mem-001"],
    })
    r = client.get(f"/api/v1/workspace/sessions/{sid}/members?path={path}")
    members = r.json()["members"]
    assert any(m["id"] == "mem-001" for m in members)


def test_add_and_remove_member(client, teamagent_dir):
    path = str(teamagent_dir.parent / "project")
    os.makedirs(path, exist_ok=True)
    sid = _create_session(client, path).json()["id"]
    client.post(f"/api/v1/workspace/sessions/{sid}/members?path={path}", json={"member_id": "mem-002"})
    r = client.get(f"/api/v1/workspace/sessions/{sid}/members?path={path}")
    assert any(m["id"] == "mem-002" for m in r.json()["members"])
    client.delete(f"/api/v1/workspace/sessions/{sid}/members/mem-002?path={path}")
    r = client.get(f"/api/v1/workspace/sessions/{sid}/members?path={path}")
    assert not any(m["id"] == "mem-002" for m in r.json()["members"])
