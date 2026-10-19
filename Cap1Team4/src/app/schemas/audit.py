from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.schemas.common import ORMModel


class AuditLogOut(ORMModel):
    id: int
    actor_id: str | None
    actor_role: str | None
    action: str
    entity_type: str
    entity_id: str | None
    old_value: dict[str, Any] | None
    new_value: dict[str, Any] | None
    ip_address: str | None
    request_id: str | None
    created_at: datetime
    prev_hash: str | None
    row_hash: str


class AuditVerification(BaseModel):
    is_valid: bool
    checked_entries: int
    first_invalid_entry_id: int | None = None
