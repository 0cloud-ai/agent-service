"""
Session Repository — 会话查询，游标分页。
"""

from __future__ import annotations

from repository.db import get_conn


def list_sessions(
    path: str,
    cursor: str | None = None,
    limit: int = 20,
    sort: str = "updated_at",
) -> dict:
    """
    返回:
        {
            "sessions": [{ id, title, created_at, updated_at, message_count }],
            "total": int,
        }
    """
    conn = get_conn()

    # 总数
    total = conn.execute(
        "SELECT count(*) FROM sessions WHERE path = ?", [path]
    ).fetchone()[0]

    # 排序字段白名单
    sort_col = sort if sort in ("updated_at", "created_at") else "updated_at"

    # 基础查询
    base_sql = f"""
        SELECT s.id, s.title, s.created_at, s.updated_at, count(m.id) AS message_count
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ?
        GROUP BY s.id, s.title, s.created_at, s.updated_at
        ORDER BY s.{sort_col} DESC, s.id DESC
    """

    rows = conn.execute(base_sql, [path]).fetchall()

    # 游标定位
    if cursor:
        found = False
        filtered = []
        for row in rows:
            if found:
                filtered.append(row)
            elif row[0] == cursor:
                found = True
        rows = filtered

    # 分页
    page = rows[:limit]
    has_more = len(rows) > limit

    sessions = [
        {
            "id": r[0],
            "title": r[1],
            "created_at": r[2],
            "updated_at": r[3],
            "message_count": r[4],
        }
        for r in page
    ]

    return {
        "sessions": sessions,
        "has_more": has_more,
        "next_cursor": sessions[-1]["id"] if has_more and sessions else None,
        "total": total,
    }


def session_exists_at(path: str) -> bool:
    """判断指定路径下是否有会话（精确匹配 path）。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE path = ? LIMIT 1", [path]
    ).fetchone()
    return row is not None
