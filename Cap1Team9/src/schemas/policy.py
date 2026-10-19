from datetime import date
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator, model_validator
from src.common.enums import PolicyType, PolicyStatus
from src.common.validators import clean_string


class PolicyCreate(BaseModel):

    customer_id: int

    policy_type: PolicyType

    coverage_limit: Decimal = Field(gt=0)

    region: str = Field(min_length=2, max_length=100)

    start_date: date

    end_date: date

    @model_validator(mode="after")
    def validate_dates(self):

        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")

        return self

    @field_validator("region")
    @classmethod
    def clean_region(cls, value):
        return clean_string(value)


class PolicyRead(BaseModel):

    id: int

    policy_number: str

    customer_id: int

    policy_type: PolicyType

    coverage_limit: Decimal

    region: str

    start_date: date

    end_date: date

    status: PolicyStatus

    model_config = {"from_attributes": True}


class PolicyUpdate(BaseModel):

    policy_type: PolicyType | None = None

    coverage_limit: Decimal | None = Field(default=None, gt=0)

    region: str | None = Field(default=None, min_length=2, max_length=100)

    start_date: date | None = None

    end_date: date | None = None

    status: PolicyStatus | None = None

    @field_validator("region")
    @classmethod
    def clean_region(cls, value):

        if value is None:
            return value

        return clean_string(value)

    @model_validator(mode="after")
    def validate_dates(self):

        if (
            self.start_date is not None
            and self.end_date is not None
            and self.start_date >= self.end_date
        ):
            raise ValueError("start_date must be before end_date")

        return self
