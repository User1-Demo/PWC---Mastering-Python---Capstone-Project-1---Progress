from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from claimiq.models.claim import ClaimStatus


class ClaimBase(BaseModel):
    claim_number: str = Field(min_length=1, max_length=50)
    policy_id: int = Field(gt=0)
    assigned_adjuster_id: int | None = Field(default=None, gt=0)
    claim_type: str = Field(min_length=1, max_length=100)
    incident_date: date
    claimed_amount: Decimal = Field(gt=0)
    description: str = Field(min_length=1)


class ClaimCreate(ClaimBase):
    pass


class ClaimUpdate(BaseModel):
    assigned_adjuster_id: int | None = Field(default=None, gt=0)
    claim_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    incident_date: date | None = None
    claimed_amount: Decimal | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, min_length=1)


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    reason: str | None = Field(default=None, max_length=1000)
    approved_amount: Decimal | None = Field(default=None, ge=0)


class ClaimResponse(ClaimBase):
    id: int
    approved_amount: Decimal | None
    status: ClaimStatus
    submitted_at: datetime
    decision_reason: str | None
    decision_date: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)