import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Enum, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import PolicyStatus, PolicyType

if TYPE_CHECKING:
    from app.models.claim import Claim


class Policy(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "policies"

    policy_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    policy_type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, native_enum=False, length=30), index=True
    )
    policyholder_name: Mapped[str] = mapped_column(String(150))
    policyholder_email: Mapped[str | None] = mapped_column(String(255))
    policyholder_phone: Mapped[str | None] = mapped_column(String(40))
    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    premium_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    deductible_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    start_date: Mapped[date] = mapped_column(Date)
    end_date: Mapped[date] = mapped_column(Date)
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, native_enum=False, length=30), default=PolicyStatus.ACTIVE, index=True
    )

    claims: Mapped[list["Claim"]] = relationship(back_populates="policy")
