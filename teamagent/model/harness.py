from pydantic import BaseModel


class PingHarnessRequest(BaseModel):
    provider: str | None = None
