"""
Domain Objects — 内部业务模型，不直接暴露给 API。
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from enum import Enum


class Vendor(str, Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GOOGLE = "google"
    OLLAMA = "ollama"


@dataclass
class User:
    id: str
    email: str
    name: str
    password: str
    created_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class Message:
    id: str
    session_id: str
    type: str = "message"  # "message" | "event"
    role: str | None = None  # "user" | "assistant" (type=message)
    content: str | None = None
    actor: str | None = None  # (type=event)
    action: str | None = None
    target: str | None = None
    detail: str | None = None
    created_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class Session:
    id: str
    title: str
    path: str
    harness: str = ""
    created_at: dt.datetime = field(default_factory=dt.datetime.now)
    updated_at: dt.datetime = field(default_factory=dt.datetime.now)
    messages: list[Message] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class DirectoryNode:
    name: str
    path: str
    children: dict[str, DirectoryNode] = field(default_factory=dict)
    sessions: list[Session] = field(default_factory=list)


@dataclass
class Member:
    id: str
    type: str  # "user" | "service"
    name: str
    # type=user
    user_id: str | None = None
    email: str | None = None
    role: str = "member"  # "owner" | "member"
    # type=service
    service_url: str | None = None
    status: str = "connected"  # "connected" | "disconnected"
    #
    joined_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class Provider:
    id: str
    vendor: Vendor
    model: str
    api_base_url: str
    api_key: str | None = None
    status: str = "unknown"
    created_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class HarnessEngine:
    id: str
    name: str
    description: str = ""
    supported_vendors: list[str] = field(default_factory=list)


@dataclass
class HarnessBinding:
    engine_id: str
    provider_id: str
    role: str = "default"


@dataclass
class Conversation:
    id: str
    title: str
    consumer_id: str
    status: str = "open"  # "open" | "escalated" | "closed"
    labels: list[str] = field(default_factory=list)
    closed_at: dt.datetime | None = None
    created_at: dt.datetime = field(default_factory=dt.datetime.now)
    updated_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class ConversationMessage:
    id: str
    conversation_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: dt.datetime = field(default_factory=dt.datetime.now)
