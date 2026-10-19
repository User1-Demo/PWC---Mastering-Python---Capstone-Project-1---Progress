from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from claimiq.core.permissions import require_admin
from claimiq.db.database import get_db
from claimiq.models.audit_log import AuditLog
from claimiq.models.user import User
from claimiq.schemas.audit_log import AuditLogResponse
from claimiq.services.audit_service import get_audit_logs

router = APIRouter(
    prefix="/api/v1/audit-logs",
    tags=["Audit Logs"],
)


AdminUser = Annotated[
    User,
    Depends(require_admin),
]


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
def list_audit_logs_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AdminUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[AuditLog]:
    return get_audit_logs(
        db=db,
        skip=skip,
        limit=limit,
    )