from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from src.common.enums import ClaimStatus


class ClaimCreate(BaseModel):
    policy_number: str
    incident_date: date
    claim_amount: Decimal


class ClaimUpdate(BaseModel):
    status: ClaimStatus
    approved_amount: Decimal | None = None


class ClaimAssignment(BaseModel):
    assigned_adjuster_id: int


class ClaimResponse(BaseModel):
    id: int
    claim_number: str
    policy_number: str
    incident_date: date
    claim_amount: Decimal
    approved_amount: Decimal | None
    status: ClaimStatus
    assigned_adjuster_id: int | None

    model_config = {"from_attributes": True}
