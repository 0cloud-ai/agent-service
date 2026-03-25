"""
Stats API — GET /api/v1/stats/{path}
树形浏览，只关心结构和计数，不返回会话详情。
"""

from fastapi import APIRouter, HTTPException

from model.dto import StatsResponseDTO
from service import stats_service

router = APIRouter(prefix="/api/v1", tags=["stats"])


@router.get("/stats", response_model=StatsResponseDTO)
@router.get("/stats/{path:path}", response_model=StatsResponseDTO)
def get_stats(path: str = "/") -> StatsResponseDTO:
    result = stats_service.get_stats(path)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found")
    return result
