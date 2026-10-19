from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    user_id: int | None
    action: str
    entity_type: str | None
    entity_id: int | None
    request_id: str | None
    metadata_json: dict[str, Any] | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)