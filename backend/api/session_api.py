"""
Session API — GET /api/v1/sessions/{path}
列出本级会话，带游标分页。
"""

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from model.dto import SessionListResponseDTO
from service import session_service

router = APIRouter(prefix="/api/v1", tags=["sessions"])


@router.get("/sessions", response_model=SessionListResponseDTO)
@router.get("/sessions/{path:path}", response_model=SessionListResponseDTO)
def list_sessions(
    path: str = "/",
    cursor: Annotated[str | None, Query(description="上一页最后一条的 id")] = None,
    limit: Annotated[int, Query(ge=1, le=100, description="每页条数")] = 20,
    sort: Annotated[
        str,
        Query(
            description="排序字段",
            pattern="^(updated_at|created_at)$",
        ),
    ] = "updated_at",
) -> SessionListResponseDTO:
    result = session_service.list_sessions(path, cursor=cursor, limit=limit, sort=sort)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Path '{path}' not found")
    return result
