from pathlib import Path
from fastapi import Request, HTTPException

from config.models import AppConfig
from service.user_service import UserService
from repository.user_repo import UserRepo


def get_config(request: Request) -> AppConfig:
    return request.app.state.config


def get_base_path(request: Request) -> Path:
    return request.app.state.base_path


def get_user_service(request: Request) -> UserService:
    if not hasattr(request.app.state, "_user_service"):
        repo = UserRepo(request.app.state.base_path)
        secret = getattr(request.app.state, "jwt_secret", "changeme")
        request.app.state._user_service = UserService(repo, jwt_secret=secret)
    return request.app.state._user_service


def get_current_user(request: Request) -> dict:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = auth[7:]
    svc = get_user_service(request)
    user = svc.verify_token(token)
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user
