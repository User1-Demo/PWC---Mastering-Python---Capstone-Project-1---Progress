from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from claimiq.db.database import Base


class ChatQueryLog(Base):
    __tablename__ = "chat_query_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    question_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    response_status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    citation_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    model_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    latency_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )