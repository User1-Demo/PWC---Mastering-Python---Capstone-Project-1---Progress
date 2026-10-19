"""Add SLA configuration table.

Revision ID: 8c3f1a6d2b90
Revises: 37e62b659613
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8c3f1a6d2b90"
down_revision: Union[str, None] = "37e62b659613"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sla_configs",
        sa.Column("claim_type", sa.Enum(
            "MOTOR", "HEALTH", "PROPERTY",
            name="policytype", native_enum=False, length=30,
        ), nullable=False),
        sa.Column("sla_days", sa.Integer(), nullable=False),
        sa.Column("updated_by", sa.Uuid(), nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.ForeignKeyConstraint(["updated_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("claim_type"),
    )


def downgrade() -> None:
    op.drop_table("sla_configs")
