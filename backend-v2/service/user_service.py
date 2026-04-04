import hashlib
import os
import uuid
from datetime import datetime, timezone, timedelta

import jwt

from repository.user_repo import UserRepo


class UserService:
    def __init__(self, repo: UserRepo, jwt_secret: str):
        self._repo = repo
        self._secret = jwt_secret

    def _hash_password(self, password: str, salt: str) -> str:
        return hashlib.sha256((salt + password).encode()).hexdigest()

    def _generate_token(self, user_id: str) -> str:
        payload = {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) + timedelta(hours=24),
        }
        return jwt.encode(payload, self._secret, algorithm="HS256")

    def register(self, email: str, password: str, name: str) -> dict:
        if self._repo.get_user_by_email(email) is not None:
            raise ValueError(f"Email '{email}' is already registered")
        user_id = f"user-{uuid.uuid4().hex[:8]}"
        salt = os.urandom(16).hex()
        now = datetime.now(timezone.utc).isoformat()
        user = {
            "id": user_id,
            "email": email,
            "name": name,
            "salt": salt,
            "password_hash": self._hash_password(password, salt),
            "created_at": now,
            "updated_at": now,
        }
        self._repo.create_user(user)
        token = self._generate_token(user_id)
        return {
            "id": user_id,
            "email": email,
            "name": name,
            "created_at": now,
            "token": token,
        }

    def login(self, email: str, password: str) -> dict:
        user = self._repo.get_user_by_email(email)
        if user is None:
            raise ValueError("Invalid email or password")
        if self._hash_password(password, user["salt"]) != user["password_hash"]:
            raise ValueError("Invalid email or password")
        token = self._generate_token(user["id"])
        return {
            "token": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "name": user["name"],
            },
        }

    def verify_token(self, token: str) -> dict | None:
        try:
            payload = jwt.decode(token, self._secret, algorithms=["HS256"])
            return self._repo.get_user_by_id(payload["sub"])
        except (jwt.InvalidTokenError, KeyError):
            return None

    def get_user(self, user_id: str) -> dict | None:
        return self._repo.get_user_by_id(user_id)

    def update_profile(self, user_id: str, data: dict) -> dict | None:
        data["updated_at"] = datetime.now(timezone.utc).isoformat()
        return self._repo.update_user(user_id, data)

    def change_password(self, user_id: str, old_password: str, new_password: str) -> None:
        user = self._repo.get_user_by_id(user_id)
        if user is None:
            raise ValueError("User not found")
        if self._hash_password(old_password, user["salt"]) != user["password_hash"]:
            raise ValueError("Invalid old password")
        salt = os.urandom(16).hex()
        self._repo.update_user(user_id, {
            "salt": salt,
            "password_hash": self._hash_password(new_password, salt),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
