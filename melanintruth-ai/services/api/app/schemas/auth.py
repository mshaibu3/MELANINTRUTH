from __future__ import annotations
from app.schemas.common import BaseModel, Field

if BaseModel is object:
    class RegisterRequest(dict):
        pass
    class LoginRequest(dict):
        pass
    class RefreshRequest(dict):
        pass
else:
    class RegisterRequest(BaseModel):
        email: str = Field(..., examples=["user@example.com"])
        password: str = Field(..., min_length=12)
        roles: list[str] = Field(default_factory=lambda: ["user"])
    class LoginRequest(BaseModel):
        email: str
        password: str
        device_label: str = "unknown"
    class RefreshRequest(BaseModel):
        refresh_token: str
        session_id: str | None = None
    class AuthTokens(BaseModel):
        access_token: str
        refresh_token: str
        session_id: str
