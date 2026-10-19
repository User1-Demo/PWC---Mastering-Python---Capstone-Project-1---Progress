from sqlalchemy import Column, String, Numeric, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.database import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    claim_number = Column(String(30), unique=True, nullable=False)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("policies.id"), nullable=False)
    claimant_name = Column(String(120), nullable=False)
    claim_type = Column(String(20), nullable=False)
    region = Column(String(50), nullable=False)
    amount_claimed = Column(Numeric(14, 2), nullable=False)
    status = Column(String(30), nullable=False, default="submitted")
    assigned_adjuster_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    submitted_at = Column(DateTime, server_default=func.now())
    sla_due_at = Column(DateTime, nullable=True)
    override_flag = Column(Boolean, default=False)
    override_justification = Column(Text, nullable=True)


class ClaimNote(Base):
    __tablename__ = "claim_notes"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    author_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    note_text = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=func.now())


class ClaimStatusHistory(Base):
    __tablename__ = "claim_status_history"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    claim_id = Column(UUID(as_uuid=True), ForeignKey("claims.id"), nullable=False)
    from_status = Column(String(30), nullable=True)
    to_status = Column(String(30), nullable=False)
    changed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, server_default=func.now())