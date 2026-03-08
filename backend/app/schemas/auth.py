"""Auth request/response schemas."""
from pydantic import BaseModel, EmailStr


class UserRegister(BaseModel):
    """Registration payload."""

    email: EmailStr
    password: str


class UserLogin(BaseModel):
    """Login payload."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"
