from fastapi import APIRouter, Depends, HTTPException, Request

from teamagent.api.deps import get_config, get_base_path
from teamagent.config.models import AppConfig
from teamagent.model.session import CreateSessionRequest, SendMessageRequest, AddMemberRequest
from teamagent.repository.session_repo import SessionRepo
from teamagent.service.session_service import SessionService
from pathlib import Path

router = APIRouter(prefix="/api/v1/workspace/sessions", tags=["workspace-sessions"])


def _get_session_service(request: Request) -> SessionService:
    repo = SessionRepo(request.app.state.base_path)
    return SessionService(repo, request.app.state.config)


@router.get("")
def list_sessions(
    path: str,
    sort: str = "updated_at",
    limit: int = 20,
    cursor: str | None = None,
    svc: SessionService = Depends(_get_session_service),
):
    return svc.list_sessions(path, sort=sort, limit=limit, cursor=cursor)


@router.post("")
def create_session(req: CreateSessionRequest, svc: SessionService = Depends(_get_session_service)):
    try:
        return svc.create_session(req.path, req.title, req.harness, req.provider, req.members)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/messages")
def get_messages(
    session_id: str,
    path: str,
    limit: int = 50,
    cursor: str | None = None,
    order: str = "asc",
    svc: SessionService = Depends(_get_session_service),
):
    try:
        return svc.get_messages(path, session_id, limit=limit, cursor=cursor, order=order)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/messages")
async def send_message(
    session_id: str,
    req: SendMessageRequest,
    path: str,
    svc: SessionService = Depends(_get_session_service),
):
    try:
        return await svc.send_message(path, session_id, req.content, req.mentions)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.get("/{session_id}/members")
def get_members(
    session_id: str,
    path: str,
    svc: SessionService = Depends(_get_session_service),
):
    try:
        return {"members": svc.get_members(path, session_id)}
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.post("/{session_id}/members")
def add_member(
    session_id: str,
    req: AddMemberRequest,
    path: str,
    svc: SessionService = Depends(_get_session_service),
):
    try:
        return svc.add_member(path, session_id, req.member_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")


@router.delete("/{session_id}/members/{member_id}", status_code=204)
def remove_member(
    session_id: str,
    member_id: str,
    path: str,
    svc: SessionService = Depends(_get_session_service),
):
    try:
        svc.remove_member(path, session_id, member_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Session not found")
