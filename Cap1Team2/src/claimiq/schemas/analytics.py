from pydantic import BaseModel, Field


class ClaimAnalyticsResponse(BaseModel):
    total_claims: int
    claims_by_status: dict[str, int]
    total_claimed_amount: float
    total_approved_amount: float
    approval_rate: float = Field(ge=0, le=100)
    rejection_rate: float = Field(ge=0, le=100)
    average_turnaround_days: float
    sla_breaches: int