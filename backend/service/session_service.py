"""
Session Service — 查询会话列表，委托 Repository 层查询 DuckDB。
"""

from __future__ import annotations

from model.dto import PaginationDTO, SessionDTO, SessionListResponseDTO
from repository import session_repo, stats_repo


def _normalize(path: str) -> str:
    if not path or path == "/":
        return "/"
    if not path.startswith("/"):
        path = "/" + path
    return path.rstrip("/")


def list_sessions(
    path: str,
    cursor: str | None = None,
    limit: int = 20,
    sort: str = "updated_at",
) -> SessionListResponseDTO | None:
    path = _normalize(path)

    # 根路径始终存在
    if path != "/" and not stats_repo.path_exists(path):
        return None

    result = session_repo.list_sessions(path, cursor=cursor, limit=limit, sort=sort)

    return SessionListResponseDTO(
        path=path,
        sessions=[
            SessionDTO(
                id=s["id"],
                title=s["title"],
                created_at=s["created_at"],
                updated_at=s["updated_at"],
                message_count=s["message_count"],
            )
            for s in result["sessions"]
        ],
        pagination=PaginationDTO(
            next_cursor=result["next_cursor"],
            has_more=result["has_more"],
            total=result["total"],
        ),
    )
