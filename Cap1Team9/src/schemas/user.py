from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from src.common.enums import UserRole
from src.common.validators import clean_string, clean_email


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    role: UserRole

    @field_validator("username")
    @classmethod
    def clean_username(cls, value):
        return clean_string(value)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value):
        return clean_email(value)


class UserRead(BaseModel):
    id: int
    username: str
    email: str
    role: str

    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    username: Optional[str] = Field(
        default=None,
        min_length=3,
        max_length=50,
    )
    email: EmailStr | None = None
    role: UserRole | None = None

    @field_validator("username")
    @classmethod
    def clean_username(cls, value):
        if value is None:
            return value
        return clean_string(value)

    @field_validator("email")
    @classmethod
    def clean_email(cls, value):
        if value is None:
            return value

        return clean_email(value)
