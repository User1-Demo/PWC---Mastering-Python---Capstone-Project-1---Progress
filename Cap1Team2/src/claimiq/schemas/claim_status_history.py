from datetime import datetime

from pydantic import BaseModel, ConfigDict

from claimiq.models.claim_status_history import (
    ClaimStatusHistoryStatus,
)


class ClaimStatusHistoryResponse(BaseModel):
    id: int
    claim_id: int
    previous_status: ClaimStatusHistoryStatus | None
    new_status: ClaimStatusHistoryStatus
    changed_by: int
    reason: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)