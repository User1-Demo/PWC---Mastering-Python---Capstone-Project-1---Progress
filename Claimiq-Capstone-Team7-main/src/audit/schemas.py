
"""
schemas.py (audit module)
"""

from datetime import datetime
from uuid import UUID
from typing import Optional, Any
from pydantic import BaseModel


class AuditLogResponse(BaseModel):
    id: UUID
    actor_id: Optional[UUID] = None
    action: str
    entity_type: str
    entity_id: Optional[UUID] = None
    metadata_json: Optional[dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True