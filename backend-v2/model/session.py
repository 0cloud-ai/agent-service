from pydantic import BaseModel


class CreateSessionRequest(BaseModel):
    path: str
    title: str | None = None
    harness: str | None = None
    members: list[str] = []


class SendMessageRequest(BaseModel):
    content: str
    mentions: list[str] = []


class AddMemberRequest(BaseModel):
    member_id: str


class SessionResponse(BaseModel):
    id: str
    title: str | None
    path: str
    harness: str
    members: list = []
    created_at: str
    updated_at: str
    message_count: int


class MessageResponse(BaseModel):
    id: str
    type: str
    role: str | None = None
    content: str | None = None
    actor: str | None = None
    action: str | None = None
    target: str | None = None
    detail: str | None = None
    created_at: str


class SessionMemberResponse(BaseModel):
    id: str
    type: str
    name: str
    joined_at: str
    joined_via: str


class PaginationResponse(BaseModel):
    next_cursor: str | None
    has_more: bool
    total: int


class SessionListResponse(BaseModel):
    path: str
    sessions: list[SessionResponse]
    pagination: PaginationResponse


class SessionMessagesResponse(BaseModel):
    session_id: str
    session: SessionResponse
    messages: list[MessageResponse]
    pagination: PaginationResponse
