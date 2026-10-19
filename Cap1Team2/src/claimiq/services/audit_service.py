from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.audit_log import AuditLog


def create_audit_log(
    db: Session,
    *,
    action: str,
    user_id: int | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    request_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Create and persist an audit-log record."""

    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        request_id=request_id,
        metadata_json=metadata,
    )

    db.add(audit_log)
    db.commit()
    db.refresh(audit_log)

    return audit_log


def get_audit_logs(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[AuditLog]:
    """Return audit logs ordered from newest to oldest."""

    statement = (
        select(AuditLog)
        .order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())