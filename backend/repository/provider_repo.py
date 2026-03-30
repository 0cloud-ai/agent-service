"""
Provider Repository — LLM 供应商的增删改查。
"""

from __future__ import annotations

from repository.db import get_conn


def _row_to_dict(row) -> dict:
    return {
        "id": row[0],
        "vendor": row[1],
        "model": row[2],
        "api_base_url": row[3],
        "api_key": row[4],
        "status": row[5],
        "created_at": row[6],
    }


def list_providers() -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, vendor, model, api_base_url, api_key, status, created_at FROM providers ORDER BY created_at DESC"
    ).fetchall()

    providers = [_row_to_dict(r) for r in rows]

    # Attach used_by (list of engine_ids) for each provider
    for p in providers:
        bindings = conn.execute(
            "SELECT engine_id FROM harness_bindings WHERE provider_id = ?",
            [p["id"]],
        ).fetchall()
        p["used_by"] = [b[0] for b in bindings]

    return providers


def get_provider(provider_id: str) -> dict | None:
    conn = get_conn()
    row = conn.execute(
        "SELECT id, vendor, model, api_base_url, api_key, status, created_at FROM providers WHERE id = ?",
        [provider_id],
    ).fetchone()
    if row is None:
        return None
    return _row_to_dict(row)


def create_provider(
    id: str,
    vendor: str,
    model: str,
    api_base_url: str,
    api_key: str | None,
    status: str = "unknown",
    created_at: str | None = None,
) -> dict:
    conn = get_conn()
    conn.execute(
        "INSERT INTO providers (id, vendor, model, api_base_url, api_key, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        [id, vendor, model, api_base_url, api_key, status, created_at],
    )
    return get_provider(id)  # type: ignore[return-value]


def update_provider(provider_id: str, **fields) -> dict | None:
    if not fields:
        return get_provider(provider_id)

    allowed = {"vendor", "model", "api_base_url", "api_key", "status"}
    updates = {k: v for k, v in fields.items() if k in allowed and v is not None}
    if not updates:
        return get_provider(provider_id)

    set_clause = ", ".join(f"{col} = ?" for col in updates)
    values = list(updates.values()) + [provider_id]

    conn = get_conn()
    conn.execute(
        f"UPDATE providers SET {set_clause} WHERE id = ?",
        values,
    )
    return get_provider(provider_id)


def delete_provider(provider_id: str) -> bool:
    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM providers WHERE id = ?", [provider_id]
    ).fetchone()
    if existing is None:
        return False
    conn.execute(
        "DELETE FROM harness_bindings WHERE provider_id = ?", [provider_id]
    )
    conn.execute("DELETE FROM providers WHERE id = ?", [provider_id])
    return True


def get_bindings_for_provider(provider_id: str) -> list[dict]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT engine_id, provider_id, role FROM harness_bindings WHERE provider_id = ?",
        [provider_id],
    ).fetchall()
    return [
        {"engine_id": r[0], "provider_id": r[1], "role": r[2]}
        for r in rows
    ]
