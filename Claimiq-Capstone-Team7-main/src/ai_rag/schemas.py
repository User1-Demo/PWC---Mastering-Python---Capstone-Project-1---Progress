"""
schemas.py (ai_rag module)
"""

from pydantic import BaseModel, Field
from typing import Optional


class AIQueryRequest(BaseModel):
    question: str = Field(..., min_length=3, max_length=1000)


class AIQueryResponse(BaseModel):
    answer: str
    source: Optional[str] = None
    confidence: str