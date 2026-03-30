"""
Workspace Providers API — /api/v1/workspace/providers
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from model.do import Vendor
from model.dto import ProviderDTO, PingResultDTO
from service import provider_service

router = APIRouter(prefix="/api/v1/workspace", tags=["workspace-providers"])


# ── Request bodies ───────────────────────────────────────────────────

class CreateProviderRequest(BaseModel):
    vendor: Vendor
    model: str
    api_base_url: str | None = None
    api_key: str | None = None


class UpdateProviderRequest(BaseModel):
    vendor: Vendor | None = None
    model: str | None = None
    api_base_url: str | None = None
    api_key: str | None = None


# ── Routes ───────────────────────────────────────────────────────────

@router.get("/providers", response_model=list[ProviderDTO])
def list_providers() -> list[ProviderDTO]:
    return provider_service.list_providers()


@router.post("/providers", response_model=ProviderDTO, status_code=201)
def create_provider(body: CreateProviderRequest) -> ProviderDTO:
    result = provider_service.create_provider(
        vendor=body.vendor,
        model=body.model,
        api_base_url=body.api_base_url,
        api_key=body.api_key,
    )
    return result


@router.put("/providers/{provider_id}", response_model=ProviderDTO)
def update_provider(provider_id: str, body: UpdateProviderRequest) -> ProviderDTO:
    result = provider_service.update_provider(
        provider_id,
        vendor=body.vendor,
        model=body.model,
        api_base_url=body.api_base_url,
        api_key=body.api_key,
    )
    return result


@router.delete("/providers/{provider_id}", status_code=204)
def delete_provider(provider_id: str) -> None:
    result = provider_service.delete_provider(provider_id)
    if result is None:
        raise HTTPException(status_code=409, detail="Provider is in use and cannot be deleted")


@router.post("/providers/{provider_id}/ping", response_model=PingResultDTO)
def ping_provider(provider_id: str) -> PingResultDTO:
    return provider_service.ping_provider(provider_id)
