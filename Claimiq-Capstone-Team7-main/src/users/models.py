"""
models.py (users module)

Purpose: Define the 'User' Python class that SQLAlchemy maps to the
'users' table you ALREADY created manually in pgAdmin.

Notice: every column here matches EXACTLY what you typed in the
CREATE TABLE statement earlier. SQLAlchemy doesn't create anything
new right now - it just needs to know the shape of the existing table
so it can translate Python code into the correct SQL.
"""

import uuid
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from src.database import Base


class User(Base):
    __tablename__ = "users"  # This MUST match your actual table name exactly

    id = Column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False)  # admin/manager/adjuster/support_agent
    region = Column(String(50), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"