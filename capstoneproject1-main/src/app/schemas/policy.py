from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.app.db.models import PolicyStatus, PolicyType


class PolicyCreate(BaseModel):
    policy_number: str = Field(
        min_length=3,
        max_length=50,
    )
    policy_type: PolicyType
    holder_name: str = Field(
        min_length=2,
        max_length=150,
    )
    region: str = Field(
        min_length=2,
        max_length=50,
    )
    coverage_start: date
    coverage_end: date
    status: PolicyStatus = PolicyStatus.ACTIVE

    @model_validator(mode="after")
    def validate_coverage_dates(self):
        if self.coverage_end <= self.coverage_start:
            raise ValueError(
                "coverage_end must be after coverage_start"
            )

        return self


class PolicyResponse(PolicyCreate):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)