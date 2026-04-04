from tests.conftest import _register, _auth_header


def test_register(client):
    r = _register(client)
    assert r.status_code == 200
    data = r.json()
    assert data["email"] == "alice@test.com"
    assert "token" in data


def test_register_duplicate(client):
    _register(client)
    r = _register(client)
    assert r.status_code == 409


def test_login(client):
    _register(client)
    r = client.post("/api/v1/user/login", json={
        "email": "alice@test.com", "password": "pass123",
    })
    assert r.status_code == 200
    assert "token" in r.json()


def test_login_wrong_password(client):
    _register(client)
    r = client.post("/api/v1/user/login", json={
        "email": "alice@test.com", "password": "wrong",
    })
    assert r.status_code == 401


def test_get_me(client):
    token = _register(client).json()["token"]
    r = client.get("/api/v1/user/me", headers=_auth_header(token))
    assert r.status_code == 200
    assert r.json()["email"] == "alice@test.com"


def test_get_me_unauthorized(client):
    r = client.get("/api/v1/user/me")
    assert r.status_code == 401


def test_update_me(client):
    token = _register(client).json()["token"]
    r = client.put("/api/v1/user/me", json={"name": "Alice Updated"}, headers=_auth_header(token))
    assert r.status_code == 200
    assert r.json()["name"] == "Alice Updated"


def test_change_password(client):
    token = _register(client).json()["token"]
    r = client.put("/api/v1/user/me/password", json={
        "old_password": "pass123", "new_password": "newpass",
    }, headers=_auth_header(token))
    assert r.status_code == 200
    r2 = client.post("/api/v1/user/login", json={
        "email": "alice@test.com", "password": "newpass",
    })
    assert r2.status_code == 200


def test_change_password_wrong_old(client):
    token = _register(client).json()["token"]
    r = client.put("/api/v1/user/me/password", json={
        "old_password": "wrong", "new_password": "newpass",
    }, headers=_auth_header(token))
    assert r.status_code == 401
