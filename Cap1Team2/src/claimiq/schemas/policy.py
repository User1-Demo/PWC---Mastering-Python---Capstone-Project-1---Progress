from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from claimiq.models.policy import PolicyStatus


class PolicyBase(BaseModel):
    policy_number: str = Field(min_length=1, max_length=50)
    policyholder_name: str = Field(min_length=2, max_length=150)
    coverage_type: str = Field(min_length=1, max_length=100)
    region: str = Field(min_length=1, max_length=100)
    coverage_limit: Decimal = Field(gt=0)
    deductible: Decimal = Field(ge=0)
    start_date: date
    end_date: date
    status: PolicyStatus = PolicyStatus.ACTIVE


class PolicyCreate(PolicyBase):
    pass


class PolicyUpdate(BaseModel):
    policyholder_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=150,
    )
    coverage_type: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    region: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
    )
    coverage_limit: Decimal | None = Field(default=None, gt=0)
    deductible: Decimal | None = Field(default=None, ge=0)
    start_date: date | None = None
    end_date: date | None = None
    status: PolicyStatus | None = None


class PolicyResponse(PolicyBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)