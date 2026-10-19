"""
schemas.py (policies module)

Purpose: Define request/response shapes for the Policies API.
Pydantic validates incoming data automatically (dates, enums, positive
numbers) before our service/router code ever runs.
"""

from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator

from src.common.enums import PolicyType, PolicyStatus


class PolicyCreate(BaseModel):
    policy_number: str = Field(..., min_length=3, max_length=30)
    type: PolicyType
    coverage_amount: float = Field(..., gt=0, description="Must be greater than 0")
    region: str = Field(..., min_length=2, max_length=50)
    start_date: date
    end_date: date

    @field_validator("end_date")
    @classmethod
    def end_date_after_start_date(cls, v, info):
        start_date = info.data.get("start_date")
        if start_date and v <= start_date:
            raise ValueError("end_date must be after start_date")
        return v


class PolicyResponse(BaseModel):
    id: UUID
    policy_number: str
    type: PolicyType
    coverage_amount: float
    region: str
    status: PolicyStatus
    start_date: date
    end_date: date
    created_at: datetime

    class Config:
        from_attributes = True


class PolicyUpdateStatus(BaseModel):
    status: PolicyStatus