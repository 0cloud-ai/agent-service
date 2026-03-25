"""
Data Transfer Objects — API 响应模型。
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel


# ── Stats ────────────────────────────────────────────────────────────

class CountsDTO(BaseModel):
    directories: int
    sessions: int
    messages: int


class ChildStatsDTO(BaseModel):
    name: str
    total: CountsDTO


class StatsResponseDTO(BaseModel):
    path: str
    direct: CountsDTO
    total: CountsDTO
    children: list[ChildStatsDTO]


# ── Sessions ─────────────────────────────────────────────────────────

class SessionDTO(BaseModel):
    id: str
    title: str
    created_at: dt.datetime
    updated_at: dt.datetime
    message_count: int


class PaginationDTO(BaseModel):
    next_cursor: str | None
    has_more: bool
    total: int


class SessionListResponseDTO(BaseModel):
    path: str
    sessions: list[SessionDTO]
    pagination: PaginationDTO
