from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy import (
    Enum as SqlEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from claimiq.db.database import Base


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    VALIDATION = "VALIDATION"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    AI_MANAGER_REVIEW = "AI_MANAGER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    claim_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
    )

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False,
        index=True,
    )

    assigned_adjuster_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    claim_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    claimed_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    approved_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    status: Mapped[ClaimStatus] = mapped_column(
        SqlEnum(ClaimStatus, name="claim_status"),
        nullable=False,
        default=ClaimStatus.SUBMITTED,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    decision_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    decision_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
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