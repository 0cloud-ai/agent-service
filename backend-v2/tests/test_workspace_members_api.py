def test_list_members(client):
    r = client.get("/api/v1/workspace/members")
    assert r.status_code == 200
    members = r.json()["members"]
    assert len(members) == 3


def test_list_members_filter_type(client):
    r = client.get("/api/v1/workspace/members?type=user")
    assert r.status_code == 200
    members = r.json()["members"]
    assert len(members) == 2
    assert all(m["type"] == "user" for m in members)


def test_list_members_filter_service(client):
    r = client.get("/api/v1/workspace/members?type=service")
    members = r.json()["members"]
    assert len(members) == 1
    assert members[0]["name"] == "Design Team"


def test_ping_not_service(client):
    r = client.post("/api/v1/workspace/members/mem-001/ping")
    assert r.status_code == 422


def test_ping_not_found(client):
    r = client.post("/api/v1/workspace/members/nonexistent/ping")
    assert r.status_code == 404
