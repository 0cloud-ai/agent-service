import pytest
from pathlib import Path

from repository.user_repo import UserRepo
from service.user_service import UserService


@pytest.fixture
def svc(tmp_path):
    (tmp_path / "users").mkdir()
    repo = UserRepo(tmp_path)
    return UserService(repo, jwt_secret="test-secret")


def test_register(svc):
    result = svc.register("alice@test.com", "password123", "Alice")
    assert result["email"] == "alice@test.com"
    assert "token" in result
    assert "id" in result


def test_register_duplicate(svc):
    svc.register("alice@test.com", "pass", "Alice")
    with pytest.raises(ValueError, match="already registered"):
        svc.register("alice@test.com", "pass", "Alice")


def test_login_success(svc):
    svc.register("alice@test.com", "password123", "Alice")
    result = svc.login("alice@test.com", "password123")
    assert "token" in result
    assert result["user"]["email"] == "alice@test.com"


def test_login_wrong_password(svc):
    svc.register("alice@test.com", "password123", "Alice")
    with pytest.raises(ValueError, match="Invalid"):
        svc.login("alice@test.com", "wrong")


def test_login_not_found(svc):
    with pytest.raises(ValueError, match="Invalid"):
        svc.login("nope@test.com", "pass")


def test_verify_token(svc):
    reg = svc.register("alice@test.com", "pass", "Alice")
    user = svc.verify_token(reg["token"])
    assert user["email"] == "alice@test.com"


def test_verify_invalid_token(svc):
    assert svc.verify_token("garbage") is None


def test_change_password(svc):
    reg = svc.register("alice@test.com", "old_pass", "Alice")
    svc.change_password(reg["id"], "old_pass", "new_pass")
    result = svc.login("alice@test.com", "new_pass")
    assert "token" in result


def test_change_password_wrong_old(svc):
    reg = svc.register("alice@test.com", "old_pass", "Alice")
    with pytest.raises(ValueError, match="Invalid"):
        svc.change_password(reg["id"], "wrong", "new_pass")
