import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import ClaimStatus, NoteType, PolicyType
from app.schemas.common import ORMModel


class ClaimCreate(BaseModel):
    claim_number: str | None = Field(default=None, max_length=50)
    policy_id: uuid.UUID
    claim_type: PolicyType
    claimant_name: str = Field(min_length=2, max_length=150)
    claimant_email: EmailStr | None = None
    claimant_phone: str | None = Field(default=None, max_length=40)
    claimant_national_id: str | None = Field(default=None, max_length=255)
    incident_date: date
    description: str = Field(min_length=1)
    claimed_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    assigned_adjuster_id: uuid.UUID | None = None

    @field_validator("incident_date")
    @classmethod
    def incident_not_in_future(cls, value: date) -> date:
        if value > date.today():
            raise ValueError("incident_date cannot be in the future")
        return value


class ClaimOut(ORMModel):
    id: uuid.UUID
    claim_number: str
    policy_id: uuid.UUID
    region_id: uuid.UUID
    claim_type: PolicyType
    status: ClaimStatus
    claimant_name: str
    claimant_email: EmailStr | None
    claimant_phone: str | None
    incident_date: date
    description: str
    claimed_amount: Decimal
    approved_amount: Decimal | None
    is_high_value: bool
    assigned_adjuster_id: uuid.UUID | None
    created_by: uuid.UUID
    submitted_at: datetime
    sla_due_at: datetime
    decided_at: datetime | None
    closed_at: datetime | None
    created_at: datetime
    updated_at: datetime


class ClaimStatusUpdate(BaseModel):
    status: ClaimStatus
    justification: str | None = Field(default=None, max_length=2000)
    note: str | None = Field(default=None, max_length=5000)
    approved_amount: Decimal | None = Field(default=None, gt=0, max_digits=14, decimal_places=2)


class ClaimAssignmentUpdate(BaseModel):
    adjuster_id: uuid.UUID | None


class ClaimStatusHistoryOut(ORMModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    from_status: ClaimStatus | None
    to_status: ClaimStatus
    changed_by: uuid.UUID
    is_override: bool
    justification: str | None
    changed_at: datetime


class ClaimNoteOut(ORMModel):
    id: uuid.UUID
    claim_id: uuid.UUID
    author_id: uuid.UUID
    note_type: NoteType
    content: str
    created_at: datetime
