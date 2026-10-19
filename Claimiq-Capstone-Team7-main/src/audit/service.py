"""
service.py (audit module)

Purpose: Central logging function used by EVERY other module.
This is the ONLY place that writes to audit_logs, and the ONLY
place that knows how to redact sensitive fields before logging.

BR-008: Sensitive personal data must never appear in logs.
FR-012/FR-013: All status changes and AI queries must be logged.
"""

from uuid import UUID
from sqlalchemy.orm import Session

from src.audit.models import AuditLog

# Field names that must NEVER appear in logged metadata, even if
# accidentally passed in. This is a safety net on top of callers
# being careful about what they pass.
SENSITIVE_KEYS = {
    "password",
    "password_hash",
    "access_token",
    "refresh_token",
    "token",
    "national_id",
    "id_number",
    "ssn",
}


def redact(metadata: dict | None) -> dict | None:
    """
    Strips any key matching SENSITIVE_KEYS (case-insensitive) from
    a metadata dict before it's ever written to the database.
    """
    if not metadata:
        return metadata

    cleaned = {}
    for key, value in metadata.items():
        if key.lower() in SENSITIVE_KEYS:
            cleaned[key] = "***REDACTED***"
        else:
            cleaned[key] = value
    return cleaned


def log_action(
    db: Session,
    actor_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None = None,
    metadata: dict | None = None,
) -> AuditLog:
    """
    The single function every module calls to record an audit event.

    Example usage (from claims/service.py):
        log_action(
            db,
            actor_id=current_user.id,
            action="claim_status_changed",
            entity_type="claim",
            entity_id=claim.id,
            metadata={"from_status": "submitted", "to_status": "validation"},
        )
    """
    safe_metadata = redact(metadata)

    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        metadata_json=safe_metadata,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def list_audit_logs(
    db: Session,
    entity_type: str | None = None,
    action: str | None = None,
    limit: int = 100,
) -> list[AuditLog]:
    query = db.query(AuditLog)

    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if action:
        query = query.filter(AuditLog.action == action)

    return query.order_by(AuditLog.created_at.desc()).limit(limit).all()