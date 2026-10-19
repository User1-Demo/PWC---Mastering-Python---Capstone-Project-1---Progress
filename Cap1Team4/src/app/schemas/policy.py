import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.models.enums import PolicyStatus, PolicyType
from app.schemas.common import ORMModel


class PolicyCreate(BaseModel):
    policy_number: str = Field(min_length=1, max_length=50)
    policy_type: PolicyType
    policyholder_name: str = Field(min_length=2, max_length=150)
    policyholder_email: EmailStr | None = None
    policyholder_phone: str | None = Field(default=None, max_length=40)
    coverage_amount: Decimal = Field(gt=0, max_digits=14, decimal_places=2)
    premium_amount: Decimal = Field(gt=0, max_digits=12, decimal_places=2)
    deductible_amount: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    region_id: uuid.UUID
    start_date: date
    end_date: date
    status: PolicyStatus = PolicyStatus.ACTIVE

    @field_validator("end_date")
    @classmethod
    def end_after_start(cls, value: date, info) -> date:
        start = info.data.get("start_date")
        if start and value < start:
            raise ValueError("end_date must not precede start_date")
        return value


class PolicyOut(ORMModel):
    id: uuid.UUID
    policy_number: str
    policy_type: PolicyType
    policyholder_name: str
    policyholder_email: EmailStr | None
    policyholder_phone: str | None
    coverage_amount: Decimal
    premium_amount: Decimal
    deductible_amount: Decimal
    region_id: uuid.UUID
    start_date: date
    end_date: date
    status: PolicyStatus
    created_at: datetime
    updated_at: datetime


class PolicyStatusUpdate(BaseModel):
    status: PolicyStatus
