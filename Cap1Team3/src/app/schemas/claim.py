from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.app.db.models import ClaimStatus, ClaimType


class ClaimCreate(BaseModel):
    claim_number: str = Field(
        min_length=3,
        max_length=50,
    )
    policy_id: int = Field(gt=0)
    claimant_name: str = Field(
        min_length=2,
        max_length=150,
    )
    claim_type: ClaimType
    region: str = Field(
        min_length=2,
        max_length=50,
    )
    amount: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    description: str = Field(
        min_length=10,
        max_length=2000,
    )
    incident_date: date


class ClaimNoteResponse(BaseModel):
    id: int
    claim_id: int
    user_id: int
    note: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimResponse(ClaimCreate):
    id: int
    status: ClaimStatus
    assigned_adjuster_id: int | None = None
    submitted_at: datetime
    closed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ClaimDetailResponse(ClaimResponse):
    notes: list[ClaimNoteResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    note: str | None = Field(
        default=None,
        min_length=3,
        max_length=2000,
    )
    manager_override: bool = False
    override_reason: str | None = Field(
        default=None,
        min_length=3,
        max_length=500,
    )