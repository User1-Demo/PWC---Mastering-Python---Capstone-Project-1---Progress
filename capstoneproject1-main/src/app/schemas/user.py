from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.app.db.models import UserRole


class UserCreate(BaseModel):
    full_name: str = Field(min_length=2, max_length=150)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: UserRole
    region: str | None = Field(default=None, min_length=2, max_length=50)


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    role: UserRole
    region: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserUpdateStatus(BaseModel):
    is_active: bool