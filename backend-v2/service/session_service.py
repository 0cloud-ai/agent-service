import uuid
from datetime import datetime, timezone
from pathlib import Path

from config.models import AppConfig
from repository.session_repo import SessionRepo


class SessionService:
    def __init__(self, repo: SessionRepo, config: AppConfig):
        self._repo = repo
        self._config = config

    def create_session(self, path: str, title: str | None, harness: str | None, members: list[str]) -> dict:
        harness_id = harness or self._config.harnesses.default
        if harness_id and harness_id not in self._config.harnesses.engines:
            raise ValueError(f"Harness '{harness_id}' not found")
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        session = {
            "id": session_id,
            "title": title,
            "path": path,
            "harness": harness_id or "",
            "members": [],
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
        }
        self._repo.create_session(Path(path), session)
        return session

    def list_sessions(self, path: str, sort: str = "updated_at", limit: int = 20, cursor: str | None = None) -> dict:
        sessions, total = self._repo.list_sessions(Path(path), sort=sort, limit=limit, cursor=cursor)
        has_more = len(sessions) < total and len(sessions) == limit
        next_cursor = sessions[-1]["id"] if has_more else None
        return {
            "path": path,
            "sessions": sessions,
            "pagination": {"next_cursor": next_cursor, "has_more": has_more, "total": total},
        }

    def get_messages(self, path: str, session_id: str, limit: int = 50, cursor: str | None = None, order: str = "asc") -> dict:
        session = self._repo.get_session(Path(path), session_id)
        if session is None:
            raise ValueError("Session not found")
        messages, total = self._repo.list_messages(Path(path), session_id, limit=limit, cursor=cursor, order=order)
        has_more = len(messages) < total and len(messages) == limit
        next_cursor = messages[-1]["id"] if has_more else None
        return {
            "session_id": session_id,
            "session": session,
            "messages": messages,
            "pagination": {"next_cursor": next_cursor, "has_more": has_more, "total": total},
        }

    def send_message(self, path: str, session_id: str, content: str, mentions: list[str] | None = None) -> dict:
        session = self._repo.get_session(Path(path), session_id)
        if session is None:
            raise ValueError("Session not found")
        msg_id = f"msg-{uuid.uuid4().hex[:8]}"
        now = datetime.now(timezone.utc).isoformat()
        message = {
            "id": msg_id,
            "type": "message",
            "role": "user",
            "content": content,
            "created_at": now,
        }
        self._repo.append_message(Path(path), session_id, message)
        if mentions:
            for mention_id in mentions:
                if mention_id.startswith("mem-"):
                    existing = [m["id"] for m in session.get("members", [])]
                    if mention_id not in existing:
                        member_entry = {"id": mention_id, "joined_at": now, "joined_via": "mention"}
                        session.setdefault("members", []).append(member_entry)
                        event = {
                            "id": f"evt-{uuid.uuid4().hex[:8]}",
                            "type": "event",
                            "actor": "system",
                            "action": "member_added",
                            "target": mention_id,
                            "detail": "mention",
                            "created_at": now,
                        }
                        self._repo.append_message(Path(path), session_id, event)
        session["updated_at"] = now
        session["message_count"] = session.get("message_count", 0) + 1
        self._repo.update_session(Path(path), session_id, session)
        return message

    def get_members(self, path: str, session_id: str) -> list[dict]:
        session = self._repo.get_session(Path(path), session_id)
        if session is None:
            raise ValueError("Session not found")
        return session.get("members", [])

    def add_member(self, path: str, session_id: str, member_id: str) -> dict:
        session = self._repo.get_session(Path(path), session_id)
        if session is None:
            raise ValueError("Session not found")
        now = datetime.now(timezone.utc).isoformat()
        member_entry = {"id": member_id, "joined_at": now, "joined_via": "manual"}
        session.setdefault("members", []).append(member_entry)
        event = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "type": "event",
            "actor": "system",
            "action": "member_added",
            "target": member_id,
            "detail": "manual",
            "created_at": now,
        }
        self._repo.append_message(Path(path), session_id, event)
        self._repo.update_session(Path(path), session_id, session)
        return member_entry

    def remove_member(self, path: str, session_id: str, member_id: str) -> None:
        session = self._repo.get_session(Path(path), session_id)
        if session is None:
            raise ValueError("Session not found")
        session["members"] = [m for m in session.get("members", []) if m["id"] != member_id]
        now = datetime.now(timezone.utc).isoformat()
        event = {
            "id": f"evt-{uuid.uuid4().hex[:8]}",
            "type": "event",
            "actor": "system",
            "action": "member_removed",
            "target": member_id,
            "created_at": now,
        }
        self._repo.append_message(Path(path), session_id, event)
        self._repo.update_session(Path(path), session_id, session)
