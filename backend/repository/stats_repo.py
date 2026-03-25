"""
Stats Repository — 用 SQL 聚合计算目录统计。

核心思路：session.path 字段是目录路径（如 '/work/alibaba/k8s'），
通过 LIKE 前缀匹配实现递归统计，无需在 Python 里递归遍历。
"""

from __future__ import annotations

from repository.db import get_conn


def path_exists(path: str) -> bool:
    """判断路径是否存在（有会话直接挂在该路径，或有子路径）。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT 1 FROM sessions WHERE path = ? OR path LIKE ? LIMIT 1",
        [path, path.rstrip("/") + "/%"],
    ).fetchone()
    return row is not None


def direct_counts(path: str) -> dict:
    """本级直属统计。"""
    conn = get_conn()
    # 直属会话和消息
    row = conn.execute("""
        SELECT
            count(DISTINCT s.id)    AS sessions,
            count(m.id)             AS messages
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ?
    """, [path]).fetchone()

    sessions = row[0]
    messages = row[1]

    # 直属子目录：取 path 下一层的 distinct 段
    prefix = path.rstrip("/") + "/"
    children = conn.execute("""
        SELECT count(DISTINCT split_part(substr(path, length(?)+1), '/', 1))
        FROM sessions
        WHERE path LIKE ?
    """, [prefix, prefix + "%"]).fetchone()

    directories = children[0]

    return {"directories": directories, "sessions": sessions, "messages": messages}


def total_counts(path: str) -> dict:
    """递归总计（本级 + 所有子级）。"""
    conn = get_conn()
    prefix = path.rstrip("/") + "/"
    row = conn.execute("""
        SELECT
            count(DISTINCT s.id)    AS sessions,
            count(m.id)             AS messages
        FROM sessions s
        LEFT JOIN messages m ON m.session_id = s.id
        WHERE s.path = ? OR s.path LIKE ?
    """, [path, prefix + "%"]).fetchone()

    sessions = row[0]
    messages = row[1]

    # 所有子目录（递归）
    dirs = conn.execute("""
        SELECT count(DISTINCT path) FROM (
            SELECT DISTINCT path FROM sessions
            WHERE path LIKE ?
        )
    """, [prefix + "%"]).fetchone()

    # directories = distinct sub-paths 的去重层级数
    # 更准确：从所有子 path 中提取所有中间目录
    all_paths = conn.execute(
        "SELECT DISTINCT path FROM sessions WHERE path LIKE ?",
        [prefix + "%"],
    ).fetchall()

    dir_set: set[str] = set()
    for (p,) in all_paths:
        # 提取从 prefix 开始的每一层中间目录
        rel = p[len(path) :].strip("/")
        parts = rel.split("/")
        for i in range(len(parts)):
            dir_set.add("/".join(parts[: i + 1]))

    directories = len(dir_set)

    return {"directories": directories, "sessions": sessions, "messages": messages}


def child_stats(path: str) -> list[dict]:
    """获取直属子目录及其递归统计。"""
    conn = get_conn()
    prefix = path.rstrip("/") + "/"

    # 找出直属子目录名
    rows = conn.execute("""
        SELECT DISTINCT split_part(substr(path, length(?)+1), '/', 1) AS child_name
        FROM sessions
        WHERE path LIKE ?
        ORDER BY child_name
    """, [prefix, prefix + "%"]).fetchall()

    results = []
    for (name,) in rows:
        child_path = path.rstrip("/") + "/" + name
        results.append({
            "name": name,
            "total": total_counts(child_path),
        })

    return results
