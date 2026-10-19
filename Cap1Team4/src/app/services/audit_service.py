import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.audit import AuditLog
from app.models.user import User


def _canonical_payload(
    *,
    action: str,
    entity_type: str,
    entity_id: str | None,
    actor_id: str | None,
    actor_role: str | None,
    old: dict[str, Any] | None,
    new: dict[str, Any] | None,
    ip_address: str | None,
    request_id: str | None,
    created_at: datetime,
) -> str:
    timestamp = created_at
    if timestamp.tzinfo is None:
        timestamp = timestamp.replace(tzinfo=UTC)
    else:
        timestamp = timestamp.astimezone(UTC)
    return json.dumps(
        {
            "a": action,
            "t": entity_type,
            "e": entity_id,
            "u": actor_id,
            "r": actor_role,
            "o": old,
            "n": new,
            "ip": ip_address,
            "request": request_id,
            "created_at": timestamp.isoformat(),
        },
        sort_keys=True,
        default=str,
    )


def log_action(
    db: Session,
    *,
    action: str,
    entity_type: str,
    entity_id: str | None = None,
    actor: User | None = None,
    old: dict[str, Any] | None = None,
    new: dict[str, Any] | None = None,
    request: Request | None = None,
) -> AuditLog:
    """Append a hash-chained audit row. Callers must pass already-sanitised values (BR-008)."""
    if db.get_bind().dialect.name == "postgresql":
        db.execute(text("LOCK TABLE audit_logs IN EXCLUSIVE MODE"))
    prev_hash = db.scalar(select(AuditLog.row_hash).order_by(AuditLog.id.desc()).limit(1))
    created_at = datetime.now(UTC)
    actor_id = str(actor.id) if actor else None
    actor_role = actor.role.value if actor else None
    ip_address = request.client.host if request and request.client else None
    request_id = request.headers.get("x-request-id") if request else None
    payload = _canonical_payload(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_id=actor_id,
        actor_role=actor_role,
        old=old,
        new=new,
        ip_address=ip_address,
        request_id=request_id,
        created_at=created_at,
    )
    row_hash = hashlib.sha256(((prev_hash or "") + payload).encode()).hexdigest()
    entry = AuditLog(
        actor_id=actor.id if actor else None,
        actor_role=actor_role,
        action=action, entity_type=entity_type, entity_id=entity_id,
        old_value=old, new_value=new,
        ip_address=ip_address,
        request_id=request_id,
        created_at=created_at,
        prev_hash=prev_hash, row_hash=row_hash,
    )
    db.add(entry)
    return entry


def verify_audit_chain(entries: list[AuditLog]) -> tuple[bool, int | None]:
    previous_hash: str | None = None
    for entry in entries:
        if entry.prev_hash != previous_hash:
            return False, entry.id
        payload = _canonical_payload(
            action=entry.action,
            entity_type=entry.entity_type,
            entity_id=entry.entity_id,
            actor_id=str(entry.actor_id) if entry.actor_id else None,
            actor_role=entry.actor_role,
            old=entry.old_value,
            new=entry.new_value,
            ip_address=entry.ip_address,
            request_id=entry.request_id,
            created_at=entry.created_at,
        )
        expected_hash = hashlib.sha256(
            ((previous_hash or "") + payload).encode()
        ).hexdigest()
        if entry.row_hash != expected_hash:
            return False, entry.id
        previous_hash = entry.row_hash
    return True, None
