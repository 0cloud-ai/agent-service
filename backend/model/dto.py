"""
Data Transfer Objects — API 响应模型。
"""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, Field

from model.do import Vendor


# ── Pagination ───────────────────────────────────────────────────────

class PaginationDTO(BaseModel):
    next_cursor: str | None
    has_more: bool
    total: int


# ── User ─────────────────────────────────────────────────────────────

class UserDTO(BaseModel):
    id: str
    email: str
    name: str
    created_at: dt.datetime


class MembershipDTO(BaseModel):
    member_id: str
    workspace_name: str
    workspace_url: str
    role: str


class UserWithMembershipsDTO(UserDTO):
    memberships: list[MembershipDTO] = []


class AuthResponseDTO(BaseModel):
    token: str
    user: UserDTO


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
    path: str | None = None
    harness: str = ""
    members: list[str] = []
    created_at: dt.datetime
    updated_at: dt.datetime
    message_count: int


class SessionListResponseDTO(BaseModel):
    path: str
    sessions: list[SessionDTO]
    pagination: PaginationDTO


# ── Messages / Events ────────────────────────────────────────────────

class MessageDTO(BaseModel):
    id: str
    type: str = "message"
    role: str | None = None
    content: str | None = None
    actor: str | None = None
    action: str | None = None
    target: str | None = None
    detail: str | None = None
    created_at: dt.datetime


class SessionMessagesResponseDTO(BaseModel):
    session_id: str
    session: SessionDTO
    messages: list[MessageDTO]
    pagination: PaginationDTO


# ── Session Members ──────────────────────────────────────────────────

class SessionMemberDTO(BaseModel):
    id: str
    type: str
    name: str
    service_url: str | None = None
    status: str | None = None
    joined_at: dt.datetime
    joined_via: str


# ── Members ──────────────────────────────────────────────────────────

class MemberDTO(BaseModel):
    id: str
    type: str
    name: str
    # type=user
    email: str | None = None
    role: str | None = None
    # type=service
    service_url: str | None = None
    service_info: dict | None = None
    status: str | None = None
    #
    joined_at: dt.datetime


# ── Providers ────────────────────────────────────────────────────────

class ProviderDTO(BaseModel):
    id: str
    vendor: Vendor
    model: str
    api_base_url: str
    status: str
    used_by: list[str] = []
    created_at: dt.datetime


class PingResultDTO(BaseModel):
    status: str
    latency_ms: int | None = None
    model: str | None = None
    message: str | None = None
    error: str | None = None


# ── Harness ──────────────────────────────────────────────────────────

class BindingDTO(BaseModel):
    provider_id: str
    vendor: Vendor
    model: str
    role: str


class EngineDTO(BaseModel):
    id: str
    name: str
    description: str
    supported_vendors: list[str]
    bindings: list[BindingDTO] = []


class HarnessResponseDTO(BaseModel):
    default: str
    engines: list[EngineDTO]


# ── Conversations (Service) ─────────────────────────────────────────

class ConversationDTO(BaseModel):
    id: str
    title: str
    status: str
    labels: list[str] = []
    closed_at: dt.datetime | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    message_count: int


class ConversationMessageDTO(BaseModel):
    id: str
    role: str
    content: str
    created_at: dt.datetime


class ConversationDetailDTO(ConversationDTO):
    messages: list[ConversationMessageDTO] = []
    pagination: PaginationDTO | None = None


# ── Service Inbox (Workspace view of conversations) ──────────────────

class ConsumerInfoDTO(BaseModel):
    user_id: str
    name: str


class SessionRefDTO(BaseModel):
    session_id: str
    session_title: str


class InboxConversationDTO(BaseModel):
    id: str
    title: str
    consumer: ConsumerInfoDTO
    status: str
    labels: list[str] = []
    closed_at: dt.datetime | None = None
    created_at: dt.datetime
    updated_at: dt.datetime
    message_count: int


class InboxConversationDetailDTO(InboxConversationDTO):
    messages: list[ConversationMessageDTO] = []
    referenced_by: list[SessionRefDTO] = []
    pagination: PaginationDTO | None = None


# ── Service Info ─────────────────────────────────────────────────────

class ServiceInfoDTO(BaseModel):
    name: str
    description: str
    status: str
    capabilities: list[str] = []
