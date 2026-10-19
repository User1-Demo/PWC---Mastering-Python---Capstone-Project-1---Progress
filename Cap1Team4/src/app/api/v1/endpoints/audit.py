from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.audit import AuditLog
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.audit import AuditLogOut, AuditVerification
from app.services.audit_service import verify_audit_chain

router = APIRouter(prefix="/audit", tags=["audit"])
admin_only = require_roles(UserRole.ADMIN)


@router.get("", response_model=list[AuditLogOut])
def list_audit_logs(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> list[AuditLog]:
    return list(
        db.scalars(
            select(AuditLog)
            .order_by(AuditLog.id.desc())
            .offset(offset)
            .limit(limit)
        )
    )


@router.get("/verify", response_model=AuditVerification)
def verify_audit_logs(
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> AuditVerification:
    entries = list(db.scalars(select(AuditLog).order_by(AuditLog.id.asc())))
    valid, first_invalid_id = verify_audit_chain(entries)
    return AuditVerification(
        is_valid=valid,
        checked_entries=len(entries),
        first_invalid_entry_id=first_invalid_id,
    )
