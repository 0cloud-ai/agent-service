from pydantic import BaseModel


class MemberResponse(BaseModel):
    id: str
    type: str
    name: str
    email: str | None = None
    role: str | None = None
    serviceUrl: str | None = None
    status: str | None = None


class PingResponse(BaseModel):
    status: str
    latency_ms: int | None = None
    model: str | None = None
    message: str | None = None
    error: str | None = None
    service_info: dict | None = None
