from pydantic import BaseModel


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UpdateProfileRequest(BaseModel):
    name: str | None = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str


class MembershipResponse(BaseModel):
    member_id: str
    workspace_name: str
    workspace_url: str
    role: str


class UserWithMembershipsResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str
    memberships: list[MembershipResponse] = []


class AuthResponse(BaseModel):
    id: str
    email: str
    name: str
    created_at: str
    token: str


class LoginResponse(BaseModel):
    token: str
    user: UserResponse
