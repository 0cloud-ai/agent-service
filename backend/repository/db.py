"""
DuckDB connection management + schema initialization.

数据库文件默认放在 backend/data/agent.duckdb，
设置 DB_PATH 环境变量可覆盖。
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "agent.duckdb"),
)

_conn: duckdb.DuckDBPyConnection | None = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(_DB_PATH)
        _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id          VARCHAR PRIMARY KEY,
            title       VARCHAR NOT NULL,
            path        VARCHAR NOT NULL,       -- 所属目录，如 '/work/alibaba'
            created_at  TIMESTAMP NOT NULL,
            updated_at  TIMESTAMP NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id          VARCHAR PRIMARY KEY,
            session_id  VARCHAR NOT NULL REFERENCES sessions(id),
            role        VARCHAR NOT NULL,        -- 'user' | 'assistant'
            content     VARCHAR NOT NULL,
            created_at  TIMESTAMP NOT NULL
        )
    """)
    # 常用索引
    conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_path ON sessions(path)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id)")


def seed_if_empty() -> None:
    """如果表为空，插入演示数据。"""
    conn = get_conn()
    count = conn.execute("SELECT count(*) FROM sessions").fetchone()[0]
    if count > 0:
        return

    _seed_data = [
        # (path, session_id, title, created, updated, msg_count)
        ("/work/alibaba", "sess_a1", "K8s 集群扩容方案讨论", "2026-03-18 09:00:00", "2026-03-18 11:00:00", 12),
        ("/work/alibaba", "sess_a2", "Nacos 配置中心迁移", "2026-03-19 14:00:00", "2026-03-20 10:00:00", 18),
        ("/work/alibaba", "sess_a3", "双十一压测预案", "2026-03-22 08:00:00", "2026-03-24 16:00:00", 28),
        ("/work/alibaba/k8s", "sess_k1", "Helm chart 多命名空间部署", "2026-03-20 10:00:00", "2026-03-24 15:30:00", 28),
        ("/work/alibaba/k8s", "sess_k2", "Ingress 灰度发布配置", "2026-03-15 08:00:00", "2026-03-15 12:00:00", 15),
        ("/work/alibaba/k8s/monitoring", "sess_km1", "Prometheus 告警规则梳理", "2026-03-10 09:00:00", "2026-03-12 18:00:00", 42),
        ("/work/alibaba/k8s/monitoring", "sess_km2", "Grafana 大盘优化", "2026-03-13 10:00:00", "2026-03-14 17:00:00", 35),
        ("/work/alibaba/k8s/cicd", "sess_kc1", "ArgoCD GitOps 流水线搭建", "2026-03-16 09:00:00", "2026-03-18 16:00:00", 55),
        ("/work/alibaba/openclaw", "sess_o1", "OpenKruise CloneSet 灰度策略", "2026-03-18 09:00:00", "2026-03-18 11:00:00", 15),
        ("/work/alibaba/openclaw", "sess_o2", "SidecarSet 注入调试", "2026-03-20 10:00:00", "2026-03-21 14:00:00", 22),
        ("/personal/blog", "sess_b1", "Hugo 博客主题定制", "2026-03-01 10:00:00", "2026-03-02 15:00:00", 20),
        ("/personal/blog", "sess_b2", "RSS 订阅功能实现", "2026-03-05 09:00:00", "2026-03-05 12:00:00", 8),
        ("/personal/dotfiles", "sess_d1", "Neovim LSP 配置优化", "2026-03-08 20:00:00", "2026-03-09 23:00:00", 32),
    ]

    for path, sid, title, created, updated, msg_count in _seed_data:
        conn.execute(
            "INSERT INTO sessions VALUES (?, ?, ?, ?, ?)",
            [sid, title, path, created, updated],
        )
        for i in range(msg_count):
            role = "user" if i % 2 == 0 else "assistant"
            conn.execute(
                "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
                [f"{sid}_m{i}", sid, role, f"msg-{i}", created],
            )
