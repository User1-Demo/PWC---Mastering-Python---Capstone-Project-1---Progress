import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.security import hash_password
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.user import RefreshToken, Region, User
from app.schemas.user import UserCreate, UserOut
from app.services.audit_service import log_action

router = APIRouter(prefix="/users", tags=["users"])
admin_only = require_roles(UserRole.ADMIN)  # BR-001


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db), _: User = Depends(admin_only)) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


@router.post("", response_model=UserOut, status_code=201)
def create_user(
    payload: UserCreate, request: Request,
    db: Session = Depends(get_db), admin: User = Depends(admin_only),
) -> User:
    email = payload.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise BusinessRuleError("A user with this email already exists")
    if payload.region_id is not None:
        region = db.get(Region, payload.region_id)
        if region is None or not region.is_active:
            raise NotFoundError("Region not found")
    user = User(
        email=email, full_name=payload.full_name, role=payload.role,
        region_id=payload.region_id, hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()
    log_action(db, action="USER_CREATED", entity_type="user", entity_id=str(user.id),
               actor=admin, new={"email": email, "role": payload.role.value}, request=request)
    db.commit()
    return user


@router.patch("/{user_id}/active", response_model=UserOut)
def set_user_active(
    user_id: uuid.UUID,
    is_active: bool,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise NotFoundError("User not found")
    if user.id == admin.id and not is_active:
        raise BusinessRuleError("Administrators cannot deactivate their own account")
    old_active = user.is_active
    user.is_active = is_active
    if not is_active:
        for token in db.scalars(
            select(RefreshToken).where(
                RefreshToken.user_id == user.id,
                RefreshToken.revoked_at.is_(None),
            )
        ):
            token.revoked_at = datetime.now(UTC)
    log_action(
        db,
        action="USER_ACTIVATED" if is_active else "USER_DEACTIVATED",
        entity_type="user",
        entity_id=str(user.id),
        actor=admin,
        old={"is_active": old_active},
        new={"is_active": is_active},
        request=request,
    )
    db.commit()
    db.refresh(user)
    return user
