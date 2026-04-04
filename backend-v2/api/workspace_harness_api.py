from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config
from config.models import AppConfig

router = APIRouter(prefix="/api/v1/workspace/harness", tags=["workspace-harness"])


@router.get("")
def list_harness(config: AppConfig = Depends(get_config)):
    engines = {}
    for name, engine in config.harnesses.engines.items():
        engines[name] = engine.model_dump()
    return {"default": config.harnesses.default, "engines": engines}


@router.get("/{harness_id}")
def get_harness(harness_id: str, config: AppConfig = Depends(get_config)):
    engine = config.harnesses.engines.get(harness_id)
    if engine is None:
        raise HTTPException(status_code=404, detail="Engine not found")
    return engine.model_dump()
