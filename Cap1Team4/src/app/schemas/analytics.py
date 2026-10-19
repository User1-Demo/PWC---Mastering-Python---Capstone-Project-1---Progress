from pydantic import BaseModel, Field


class AnalyticsPoint(BaseModel):
    label: str
    count: int


class ClaimsAnalytics(BaseModel):
    total_claims: int
    approved_claims: int
    rejected_claims: int
    approval_rate: float
    average_turnaround_hours: float | None
    sla_compliance_rate: float | None
    open_claims: int
    sla_breached_claims: int = 0
    by_month: list[AnalyticsPoint] = Field(default_factory=list)
    by_region: list[AnalyticsPoint] = Field(default_factory=list)
    by_claim_type: list[AnalyticsPoint] = Field(default_factory=list)
    adjuster_workload: list[AnalyticsPoint] = Field(default_factory=list)


class AIAnalytics(BaseModel):
    total_queries: int
    no_match_queries: int
    flagged_queries: int
    by_month: list[AnalyticsPoint] = Field(default_factory=list)
    top_terms: list[AnalyticsPoint] = Field(default_factory=list)
