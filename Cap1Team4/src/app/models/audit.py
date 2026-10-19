import uuid
from datetime import datetime

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, UUIDMixin

_BigPK = BigInteger().with_variant(Integer, "sqlite")


class AuditLog(Base):
    """Append-only, hash-chained: row_hash = sha256(prev_hash + canonical payload)."""

    __tablename__ = "audit_logs"
    id: Mapped[int] = mapped_column(_BigPK, primary_key=True, autoincrement=True)
    actor_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), index=True)
    actor_role: Mapped[str | None] = mapped_column(String(30))
    action: Mapped[str] = mapped_column(String(50), index=True)  # e.g. CLAIM_STATUS_CHANGED
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), index=True)
    old_value: Mapped[dict | None] = mapped_column(JSON)
    new_value: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    request_id: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    prev_hash: Mapped[str | None] = mapped_column(String(64))
    row_hash: Mapped[str] = mapped_column(String(64))


class ChatQueryLog(UUIDMixin, Base):
    __tablename__ = "chat_query_logs"
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), index=True)
    question: Mapped[str] = mapped_column(Text)  # PII-scrubbed
    answer: Mapped[str | None] = mapped_column(Text)
    source_chunk_ids: Mapped[list | None] = mapped_column(JSON)  # cited chunk/doc/section refs
    similarity_scores: Mapped[list | None] = mapped_column(JSON)
    top_k: Mapped[int | None]
    confidence_score: Mapped[float | None]
    is_no_match: Mapped[bool] = mapped_column(default=False)
    flagged_for_review: Mapped[bool] = mapped_column(default=False, index=True)
    model_name: Mapped[str | None] = mapped_column(String(100))
    prompt_tokens: Mapped[int | None]
    completion_tokens: Mapped[int | None]
    total_tokens: Mapped[int | None]
    latency_ms: Mapped[int | None]
    status: Mapped[str] = mapped_column(String(20), default="success")  # success | error
    error_type: Mapped[str | None] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
