from sqlalchemy import Column, String, Numeric, Date, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from src.database import Base


class Policy(Base):
    __tablename__ = "policies"

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    policy_number = Column(String(30), unique=True, nullable=False)
    type = Column(String(20), nullable=False)          # motor / health / property
    coverage_amount = Column(Numeric(14, 2), nullable=False)
    region = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active / inactive
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now())