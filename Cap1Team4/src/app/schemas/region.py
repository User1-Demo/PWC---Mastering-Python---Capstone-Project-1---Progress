import uuid

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class RegionCreate(BaseModel):
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z0-9_-]+$")
    name: str = Field(min_length=2, max_length=100)


class RegionOut(ORMModel):
    id: uuid.UUID
    code: str
    name: str
    is_active: bool
