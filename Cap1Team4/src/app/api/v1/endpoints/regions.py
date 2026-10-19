from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.exceptions import BusinessRuleError
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import Region, User
from app.schemas.region import RegionCreate, RegionOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/regions", tags=["regions"])
admin_only = require_roles(UserRole.ADMIN)


@router.get("", response_model=list[RegionOut])
def list_regions(
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> list[Region]:
    return list(db.scalars(select(Region).order_by(Region.name)))


@router.post("", response_model=RegionOut, status_code=201)
def create_region(
    payload: RegionCreate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> Region:
    if db.scalar(select(Region).where(Region.code == payload.code)):
        raise BusinessRuleError("A region with this code already exists")
    region = Region(code=payload.code, name=payload.name)
    db.add(region)
    db.flush()
    log_action(
        db,
        action="REGION_CREATED",
        entity_type="region",
        entity_id=str(region.id),
        actor=admin,
        new={"code": region.code, "name": region.name},
        request=request,
    )
    db.commit()
    db.refresh(region)
    return region
