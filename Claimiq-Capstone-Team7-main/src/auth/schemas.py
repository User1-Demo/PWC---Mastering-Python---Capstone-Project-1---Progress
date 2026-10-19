"""
schemas.py (auth module)

Purpose: Define the exact shape of data for login requests/responses.
FastAPI uses these Pydantic models to automatically validate incoming
JSON and auto-generate API documentation (Swagger).
"""

from pydantic import BaseModel, EmailStr
from uuid import UUID
from typing import Optional

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: str


class RefreshRequest(BaseModel):
    refresh_token: str


class UserMeResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    role: str
    region: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True  # lets Pydantic read directly from the SQLAlchemy User object