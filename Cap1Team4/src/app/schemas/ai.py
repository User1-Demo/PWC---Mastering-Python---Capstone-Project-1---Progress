import uuid

from pydantic import BaseModel, Field

from app.models.enums import PolicyType

class Citation(BaseModel):
    document_id: uuid.UUID
    document_title: str
    chunk_id: uuid.UUID
    section_heading: str | None = None
    page_number: int | None = None
    score: float


class ChatQuery(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    top_k: int = Field(default=4, ge=1, le=20)
    policy_type: PolicyType | None = None


class ChatQueryOut(BaseModel):
    answer: str
    citations: list[Citation] = Field(default_factory=list)
    no_match: bool
