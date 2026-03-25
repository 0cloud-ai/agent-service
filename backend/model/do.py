"""
Domain Objects — 内部业务模型，不直接暴露给 API。
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field


@dataclass
class Message:
    id: str
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    created_at: dt.datetime = field(default_factory=dt.datetime.now)


@dataclass
class Session:
    id: str
    title: str
    path: str  # 所属目录路径，如 "/work/alibaba"
    created_at: dt.datetime = field(default_factory=dt.datetime.now)
    updated_at: dt.datetime = field(default_factory=dt.datetime.now)
    messages: list[Message] = field(default_factory=list)

    @property
    def message_count(self) -> int:
        return len(self.messages)


@dataclass
class DirectoryNode:
    """目录树节点，持有直属会话和子目录引用。"""

    name: str
    path: str  # 完整路径，如 "/work/alibaba/k8s"
    children: dict[str, DirectoryNode] = field(default_factory=dict)
    sessions: list[Session] = field(default_factory=list)
