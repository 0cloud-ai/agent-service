import pytest
from pathlib import Path

from repository.user_repo import UserRepo


@pytest.fixture
def repo(tmp_path):
    users_dir = tmp_path / "users"
    users_dir.mkdir()
    return UserRepo(tmp_path)


def test_create_and_get_by_id(repo):
    user = {
        "id": "user-001",
        "email": "alice@test.com",
        "name": "Alice",
        "salt": "abc",
        "password_hash": "hash123",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    repo.create_user(user)
    result = repo.get_user_by_id("user-001")
    assert result["email"] == "alice@test.com"


def test_get_by_id_not_found(repo):
    assert repo.get_user_by_id("nope") is None


def test_get_by_email(repo):
    user = {
        "id": "user-001",
        "email": "alice@test.com",
        "name": "Alice",
        "salt": "abc",
        "password_hash": "hash123",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    repo.create_user(user)
    result = repo.get_user_by_email("alice@test.com")
    assert result["id"] == "user-001"


def test_get_by_email_not_found(repo):
    assert repo.get_user_by_email("nope@test.com") is None


def test_update_user(repo):
    user = {
        "id": "user-001",
        "email": "alice@test.com",
        "name": "Alice",
        "salt": "abc",
        "password_hash": "hash123",
        "created_at": "2026-01-01T00:00:00Z",
        "updated_at": "2026-01-01T00:00:00Z",
    }
    repo.create_user(user)
    repo.update_user("user-001", {"name": "Alice Updated"})
    result = repo.get_user_by_id("user-001")
    assert result["name"] == "Alice Updated"
    assert result["email"] == "alice@test.com"


def test_list_users(repo):
    for i in range(3):
        repo.create_user({
            "id": f"user-{i:03d}",
            "email": f"user{i}@test.com",
            "name": f"User {i}",
            "salt": "s",
            "password_hash": "h",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        })
    users = repo.list_users()
    assert len(users) == 3
