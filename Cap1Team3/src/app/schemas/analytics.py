from pydantic import BaseModel


class ClaimsAnalyticsResponse(BaseModel):
    total_claims: int
    approved_claims: int
    rejected_claims: int
    closed_claims: int
    approval_rate: float
    rejection_rate: float
    average_turnaround_days: float
    sla_breached_claims: int
    claims_by_status: dict[str, int]
    claims_by_region: dict[str, int]
    claims_by_type: dict[str, int]
    monthly_claim_volume: dict[str, int]
    adjuster_workload: dict[str, int]