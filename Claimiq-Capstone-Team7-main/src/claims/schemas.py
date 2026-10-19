"""
schemas.py (claims module)
"""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field, field_validator

from src.common.enums import PolicyType, ClaimStatus


class ClaimCreate(BaseModel):
    policy_id: UUID
    claimant_name: str = Field(..., min_length=2, max_length=120)
    claim_type: PolicyType
    amount_claimed: float = Field(..., gt=0, description="Must be greater than 0")


class ClaimResponse(BaseModel):
    id: UUID
    claim_number: str
    policy_id: UUID
    claimant_name: str
    claim_type: str
    region: str
    amount_claimed: float
    status: str
    assigned_adjuster_id: Optional[UUID] = None
    submitted_at: datetime
    sla_due_at: Optional[datetime] = None
    override_flag: bool
    override_justification: Optional[str] = None

    class Config:
        from_attributes = True


class ClaimStatusUpdate(BaseModel):
    to_status: ClaimStatus
    note: Optional[str] = None
    assigned_adjuster_id: Optional[UUID] = None
    override_flag: bool = False
    override_justification: Optional[str] = None

    @field_validator("override_justification")
    @classmethod
    def justification_required_if_override(cls, v, info):
        override_flag = info.data.get("override_flag")
        if override_flag and (not v or not v.strip()):
            raise ValueError(
                "override_justification is required when override_flag is true"
            )
        return v


class ClaimNoteResponse(BaseModel):
    id: UUID
    claim_id: UUID
    author_id: UUID
    note_text: str
    created_at: datetime

    class Config:
        from_attributes = True