from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Date, DateTime, Numeric, String, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from claimiq.db.database import Base


class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    SUSPENDED = "SUSPENDED"


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    policy_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    policyholder_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    coverage_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    coverage_limit: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    deductible: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[PolicyStatus] = mapped_column(
        SqlEnum(PolicyStatus, name="policy_status"),
        nullable=False,
        default=PolicyStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )