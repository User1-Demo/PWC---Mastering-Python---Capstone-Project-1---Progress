from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.core.security import get_current_user
from src.app.db.models import AuditLog, User, UserRole
from src.app.db.session import get_db
from src.app.schemas.audit import AuditLogResponse

router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def list_audit_logs(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can view audit logs",
        )

    query = select(AuditLog).order_by(AuditLog.created_at.desc())

    if action:
        query = query.where(AuditLog.action == action)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)

    return db.scalars(query).all()