import json
from pathlib import Path

from repository.file_utils import atomic_write


class UserRepo:
    def __init__(self, base_path: Path):
        self._dir = base_path / "users"

    def create_user(self, user: dict) -> None:
        path = self._dir / f"{user['id']}.json"
        atomic_write(path, user)

    def get_user_by_id(self, user_id: str) -> dict | None:
        path = self._dir / f"{user_id}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def get_user_by_email(self, email: str) -> dict | None:
        for path in self._dir.glob("*.json"):
            user = json.loads(path.read_text(encoding="utf-8"))
            if user.get("email") == email:
                return user
        return None

    def update_user(self, user_id: str, data: dict) -> dict | None:
        user = self.get_user_by_id(user_id)
        if user is None:
            return None
        user.update(data)
        atomic_write(self._dir / f"{user_id}.json", user)
        return user

    def list_users(self) -> list[dict]:
        users = []
        for path in self._dir.glob("*.json"):
            users.append(json.loads(path.read_text(encoding="utf-8")))
        return users
