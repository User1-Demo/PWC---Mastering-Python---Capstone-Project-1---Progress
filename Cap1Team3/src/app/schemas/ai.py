from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIQueryRequest(BaseModel):
    question: str = Field(min_length=5, max_length=2000)
    top_k: int = Field(default=3, ge=1, le=10)


class AIQueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence_flag: str | None = None


class ChatQueryLogResponse(BaseModel):
    id: int
    user_id: int
    question: str
    answer: str | None
    source_reference: str | None
    confidence_flag: str | None
    tokens_used: int | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)