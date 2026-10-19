"""
schemas.py (documents module)
"""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: UUID
    title: str
    file_path: str
    uploaded_by: UUID
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True