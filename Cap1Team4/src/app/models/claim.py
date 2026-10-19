import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDMixin
from app.models.enums import ClaimStatus, NoteType, PolicyType

if TYPE_CHECKING:
    from app.models.policy import Policy


class Claim(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "claims"
    __table_args__ = (CheckConstraint("claimed_amount > 0", name="ck_claim_positive_amount"),)

    claim_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    policy_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("policies.id"), index=True)
    region_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("regions.id"), index=True)
    claim_type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, native_enum=False, length=30), index=True
    )
    status: Mapped[ClaimStatus] = mapped_column(
        Enum(ClaimStatus, native_enum=False, length=30),
        default=ClaimStatus.SUBMITTED,
        index=True,
    )
    claimant_name: Mapped[str] = mapped_column(String(150), index=True)
    claimant_email: Mapped[str | None] = mapped_column(String(255))
    claimant_phone: Mapped[str | None] = mapped_column(String(40))
    claimant_national_id_enc: Mapped[str | None] = mapped_column(Text)
    incident_date: Mapped[date] = mapped_column(Date)
    description: Mapped[str] = mapped_column(Text)
    claimed_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    approved_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    is_high_value: Mapped[bool] = mapped_column(default=False, index=True)
    assigned_adjuster_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"))
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sla_due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    fraud_score: Mapped[int] = mapped_column(Integer, default=0)
    fraud_flags: Mapped[list | None] = mapped_column(JSON)

    policy: Mapped["Policy"] = relationship(back_populates="claims")
    notes: Mapped[list["ClaimNote"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan"
    )
    status_history: Mapped[list["ClaimStatusHistory"]] = relationship(
        back_populates="claim", cascade="all, delete-orphan", order_by="ClaimStatusHistory.changed_at"
    )


class ClaimNote(UUIDMixin, Base):
    __tablename__ = "claim_notes"

    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), index=True)
    author_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    note_type: Mapped[NoteType] = mapped_column(
        Enum(NoteType, native_enum=False, length=30), default=NoteType.ADJUSTER_NOTE
    )
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim: Mapped[Claim] = relationship(back_populates="notes")


class ClaimStatusHistory(UUIDMixin, Base):
    __tablename__ = "claim_status_history"

    claim_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("claims.id"), index=True)
    from_status: Mapped[ClaimStatus | None] = mapped_column(
        Enum(ClaimStatus, native_enum=False, length=30)
    )
    to_status: Mapped[ClaimStatus] = mapped_column(Enum(ClaimStatus, native_enum=False, length=30))
    changed_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    is_override: Mapped[bool] = mapped_column(default=False)
    justification: Mapped[str | None] = mapped_column(Text)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    claim: Mapped[Claim] = relationship(back_populates="status_history")


class SlaConfig(UUIDMixin, Base):
    __tablename__ = "sla_configs"

    claim_type: Mapped[PolicyType] = mapped_column(
        Enum(PolicyType, native_enum=False, length=30), unique=True
    )
    sla_days: Mapped[int] = mapped_column(Integer)
    updated_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
