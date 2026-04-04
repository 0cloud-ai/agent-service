from fastapi import APIRouter, Depends, HTTPException

from api.deps import get_user_service, get_current_user
from model.user import (
    RegisterRequest, LoginRequest, UpdateProfileRequest,
    ChangePasswordRequest, AuthResponse, LoginResponse,
    UserResponse, UserWithMembershipsResponse,
)
from service.user_service import UserService

router = APIRouter(prefix="/api/v1/user", tags=["user"])


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, svc: UserService = Depends(get_user_service)):
    try:
        return svc.register(req.email, req.password, req.name)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, svc: UserService = Depends(get_user_service)):
    try:
        return svc.login(req.email, req.password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid email or password")


@router.post("/logout")
def logout():
    return {"message": "已退出登录"}


@router.get("/me", response_model=UserWithMembershipsResponse)
def get_me(user: dict = Depends(get_current_user)):
    return {
        "id": user["id"],
        "email": user["email"],
        "name": user["name"],
        "created_at": user["created_at"],
        "memberships": [],
    }


@router.put("/me", response_model=UserResponse)
def update_me(
    req: UpdateProfileRequest,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    updates = req.model_dump(exclude_none=True)
    result = svc.update_profile(user["id"], updates)
    return {
        "id": result["id"],
        "email": result["email"],
        "name": result["name"],
        "created_at": result["created_at"],
    }


@router.put("/me/password")
def change_password(
    req: ChangePasswordRequest,
    user: dict = Depends(get_current_user),
    svc: UserService = Depends(get_user_service),
):
    try:
        svc.change_password(user["id"], req.old_password, req.new_password)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid old password")
    return {"message": "密码已更新"}
