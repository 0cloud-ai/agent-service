from pydantic import BaseModel


class CreateConversationRequest(BaseModel):
    message: str
    labels: list[str] = []


class SendConversationMessageRequest(BaseModel):
    content: str


class UpdateLabelsRequest(BaseModel):
    labels: list[str]


class EscalateRequest(BaseModel):
    reason: str | None = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    status: str
    labels: list[str]
    created_at: str
    updated_at: str
    closed_at: str | None = None
    message_count: int


class ConversationMessageResponse(BaseModel):
    id: str
    role: str
    content: str
    created_at: str


class ConsumerInfo(BaseModel):
    user_id: str
    name: str


class WorkspaceConversationResponse(BaseModel):
    id: str
    title: str
    consumer: ConsumerInfo
    status: str
    labels: list[str]
    created_at: str
    updated_at: str
    closed_at: str | None = None
    message_count: int


class ConversationDetailResponse(BaseModel):
    id: str
    title: str
    status: str
    labels: list[str]
    created_at: str
    updated_at: str
    closed_at: str | None = None
    messages: list[ConversationMessageResponse]
    pagination: dict


class SessionRef(BaseModel):
    session_id: str
    session_title: str


class WorkspaceConversationDetailResponse(BaseModel):
    id: str
    title: str
    consumer: ConsumerInfo
    status: str
    labels: list[str]
    created_at: str
    updated_at: str
    closed_at: str | None = None
    messages: list[ConversationMessageResponse]
    referenced_by: list[SessionRef] = []
    pagination: dict
