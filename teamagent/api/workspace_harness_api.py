from fastapi import APIRouter, Depends, HTTPException

from teamagent.api.deps import get_config
from teamagent.config.models import AppConfig
from teamagent.harness.registry import list_engines, get_engine
from teamagent.model.harness import PingHarnessRequest
from teamagent.service.harness_service import HarnessService

router = APIRouter(prefix="/api/v1/workspace/harness", tags=["workspace-harness"])

_harness_svc = HarnessService()


@router.get("")
def list_harness():
    engines = {}
    for engine_id, cls in list_engines().items():
        engines[engine_id] = {
            "id": cls.id,
            "name": cls.name,
            "api_formats": cls.api_formats,
        }
    return {"engines": engines}


@router.get("/{harness_id}")
def get_harness(harness_id: str):
    engine = get_engine(harness_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Engine not found")
    return {
        "id": engine.id,
        "name": engine.name,
        "api_formats": engine.api_formats,
    }


@router.post("/{harness_id}/ping")
async def ping_harness(
    harness_id: str,
    req: PingHarnessRequest | None = None,
    config: AppConfig = Depends(get_config),
):
    engine = get_engine(harness_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Engine not found")
    provider_name = req.provider if req else None
    return await _harness_svc.ping(harness_id, provider_name, config)
