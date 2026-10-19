from datetime import date, datetime, UTC
from decimal import Decimal

from sqlalchemy import (
    String,
    Date,
    Numeric,
    Enum,
    ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.common.enums import ClaimStatus
from src.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)

    claim_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    policy = relationship("Policy", back_populates="claims")

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

    assigned_adjuster = relationship(
        "User",
        back_populates="assigned_claims",
    )

    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    claim_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    approved_amount: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus),
        nullable=False,
        default=ClaimStatus.submitted,
    )

    @property
    def policy_number(self) -> str:
        return self.policy.policy_number
