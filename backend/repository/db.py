"""
DuckDB connection management + schema initialization.

DuckDB 是统一存储层，各数据源 (Claude Agent SDK, OpenCode, …)
通过各自的 adapter 把会话同步写入这里。
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb

_DB_PATH = os.environ.get(
    "DB_PATH",
    str(Path(__file__).resolve().parent.parent / "data" / "agent.duckdb"),
)

_SQL_PATH = Path(__file__).resolve().parent / "init_db.sql"

_conn: duckdb.DuckDBPyConnection | None = None


def get_conn() -> duckdb.DuckDBPyConnection:
    global _conn
    if _conn is None:
        Path(_DB_PATH).parent.mkdir(parents=True, exist_ok=True)
        _conn = duckdb.connect(_DB_PATH)
        _init_schema(_conn)
    return _conn


def reset_conn() -> None:
    """Close and reset the connection. Used in tests."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None


def get_test_conn() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB for testing."""
    global _conn
    _conn = duckdb.connect(":memory:")
    _init_schema(_conn)
    return _conn


def _init_schema(conn: duckdb.DuckDBPyConnection) -> None:
    sql = _SQL_PATH.read_text(encoding="utf-8")
    conn.execute(sql)
