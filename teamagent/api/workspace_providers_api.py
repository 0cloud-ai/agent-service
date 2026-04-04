from fastapi import APIRouter, Depends, HTTPException

from teamagent.api.deps import get_config
from teamagent.config.models import AppConfig
from teamagent.service.provider_service import ProviderService

router = APIRouter(prefix="/api/v1/workspace/providers", tags=["workspace-providers"])
_provider_svc = ProviderService()


@router.get("")
def list_providers(config: AppConfig = Depends(get_config)):
    result = {}
    for name, provider in config.providers.items():
        result[name] = {
            "baseUrl": provider.baseUrl,
            "apiFormat": provider.apiFormat,
            "status": "unknown",
            "models": [m.model_dump() for m in provider.models],
        }
    return {"providers": result}


@router.post("/{provider_name}/ping")
async def ping_provider(
    provider_name: str,
    body: dict | None = None,
    config: AppConfig = Depends(get_config),
):
    provider = config.providers.get(provider_name)
    if provider is None:
        raise HTTPException(status_code=404, detail="Provider not found")
    model_id = (body or {}).get("model")
    if not model_id and provider.models:
        model_id = provider.models[0].id
    result = await _provider_svc.ping(provider.baseUrl, provider.apiKey, provider.apiFormat, model_id)
    result["provider"] = provider_name
    result["model"] = model_id
    return result
