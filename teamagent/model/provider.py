from pydantic import BaseModel


class PingProviderRequest(BaseModel):
    model: str | None = None
