"""
router.py (audit module)

Purpose: Admin-only visibility into the audit trail.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.users.models import User
from src.auth.dependencies import require_role
from src.audit.schemas import AuditLogResponse
from src.audit import service

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("", response_model=list[AuditLogResponse])
def list_audit_logs(
    entity_type: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    limit: int = Query(100, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.list_audit_logs(db, entity_type=entity_type, action=action, limit=limit)