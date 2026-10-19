from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column

from claimiq.db.database import Base


class ClaimStatusHistoryStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    VALIDATION = "VALIDATION"
    ASSIGNED = "ASSIGNED"
    UNDER_REVIEW = "UNDER_REVIEW"
    AI_MANAGER_REVIEW = "AI_MANAGER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    previous_status: Mapped[ClaimStatusHistoryStatus | None] = mapped_column(
        SqlEnum(
            ClaimStatusHistoryStatus,
            name="claim_status_history_previous_status",
        ),
        nullable=True,
    )

    new_status: Mapped[ClaimStatusHistoryStatus] = mapped_column(
        SqlEnum(
            ClaimStatusHistoryStatus,
            name="claim_status_history_new_status",
        ),
        nullable=False,
    )

    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )