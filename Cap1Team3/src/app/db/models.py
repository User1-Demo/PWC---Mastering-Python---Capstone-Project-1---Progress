from datetime import date, datetime
from decimal import Decimal
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, Enum as SqlEnum
from sqlalchemy import ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.db.session import Base


class PolicyType(str, Enum):
    MOTOR = "MOTOR"
    HEALTH = "HEALTH"
    PROPERTY = "PROPERTY"


class PolicyStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class ClaimType(str, Enum):
    MOTOR = "MOTOR"
    HEALTH = "HEALTH"
    PROPERTY = "PROPERTY"


class ClaimStatus(str, Enum):
    SUBMITTED = "SUBMITTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CLOSED = "CLOSED"


class UserRole(str, Enum):
    ADMIN = "admin"
    CLAIMS_MANAGER = "claims_manager"
    CLAIMS_ADJUSTER = "claims_adjuster"
    SUPPORT_AGENT = "support_agent"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)

    full_name: Mapped[str] = mapped_column(String(150), nullable=False)

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SqlEnum(UserRole),
        nullable=False,
        index=True,
    )

    region: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    assigned_claims: Mapped[list["Claim"]] = relationship(
        back_populates="assigned_adjuster",
        foreign_keys="Claim.assigned_adjuster_id",
    )

    claim_notes: Mapped[list["ClaimNote"]] = relationship(
        back_populates="user",
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="user",
    )


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True)

    policy_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    policy_type: Mapped[PolicyType] = mapped_column(
        SqlEnum(PolicyType),
        nullable=False,
    )

    holder_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    coverage_start: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    coverage_end: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[PolicyStatus] = mapped_column(
        SqlEnum(PolicyStatus),
        nullable=False,
        default=PolicyStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    claims: Mapped[list["Claim"]] = relationship(
        back_populates="policy"
    )


class Claim(Base):
    __tablename__ = "claims"

    id: Mapped[int] = mapped_column(primary_key=True)

    claim_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id"),
        nullable=False,
    )

    claimant_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    claim_type: Mapped[ClaimType] = mapped_column(
        SqlEnum(ClaimType),
        nullable=False,
    )

    region: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    incident_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
    )

    status: Mapped[ClaimStatus] = mapped_column(
        SqlEnum(ClaimStatus),
        nullable=False,
        default=ClaimStatus.SUBMITTED,
    )

    assigned_adjuster_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    policy: Mapped[Policy] = relationship(
        back_populates="claims"
    )

    assigned_adjuster: Mapped[User | None] = relationship(
        back_populates="assigned_claims",
        foreign_keys=[assigned_adjuster_id],
    )

    notes: Mapped[list["ClaimNote"]] = relationship(
        back_populates="claim",
        cascade="all, delete-orphan",
        order_by="ClaimNote.created_at",
    )


class ClaimNote(Base):
    __tablename__ = "claim_notes"

    id: Mapped[int] = mapped_column(primary_key=True)

    claim_id: Mapped[int] = mapped_column(
        ForeignKey("claims.id"),
        nullable=False,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    note: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    claim: Mapped[Claim] = relationship(
        back_populates="notes"
    )

    user: Mapped[User] = relationship(
        back_populates="claim_notes"
    )


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    entity_id: Mapped[int | None] = mapped_column(
        nullable=True,
        index=True,
    )

    details: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    user: Mapped[User | None] = relationship(
        back_populates="audit_logs"
    )

class DocumentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    filename: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    file_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    uploaded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[DocumentStatus] = mapped_column(
        SqlEnum(DocumentStatus),
        nullable=False,
        default=DocumentStatus.ACTIVE,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index",
    )


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        nullable=False,
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(
        nullable=False,
    )

    chunk_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    section_ref: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    embedding_status: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        default="pending",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    document: Mapped["Document"] = relationship(
        back_populates="chunks"
    )

class ChatQueryLog(Base):
    __tablename__ = "chat_query_logs"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    question: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    answer: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    source_reference: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    confidence_flag: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    tokens_used: Mapped[int | None] = mapped_column(
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )