from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_config
from config.models import AppConfig
from service.member_service import MemberService

router = APIRouter(prefix="/api/v1/workspace/members", tags=["workspace-members"])
_member_svc = MemberService()


@router.get("")
def list_members(type: str | None = None, config: AppConfig = Depends(get_config)):
    members = _member_svc.list_members(config, type_filter=type)
    return {"members": [m.model_dump(exclude_none=True) for m in members]}


@router.post("/{member_id}/ping")
async def ping_member(member_id: str, config: AppConfig = Depends(get_config)):
    member = next((m for m in config.members if m.id == member_id), None)
    if member is None:
        raise HTTPException(status_code=404, detail="Member not found")
    if member.type != "service":
        raise HTTPException(status_code=422, detail="ping only supports type=service")
    return await _member_svc.ping(member)
