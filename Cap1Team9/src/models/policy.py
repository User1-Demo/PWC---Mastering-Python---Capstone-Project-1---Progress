from datetime import date, datetime, UTC
from sqlalchemy import String, Date, DateTime, Numeric, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from decimal import Decimal

from src.common.enums import PolicyType, PolicyStatus
from src.db.base import Base


class Policy(Base):

    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)

    policy_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    policy_type: Mapped[PolicyType] = mapped_column(Enum(PolicyType), nullable=False)

    coverage_limit: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    region: Mapped[str] = mapped_column(String(100), nullable=False)

    start_date: Mapped[date] = mapped_column(Date, nullable=False)

    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus), nullable=False, default=PolicyStatus.active
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )

    claims = relationship(
        "Claim",
        back_populates="policy",
        cascade="all, delete-orphan",
    )

    customer = relationship("User", back_populates="policies")
