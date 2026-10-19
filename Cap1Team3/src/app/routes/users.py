from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.app.core.security import get_current_user, hash_password
from src.app.db.models import User, UserRole
from src.app.db.session import get_db
from src.app.schemas.user import UserCreate, UserResponse, UserUpdateStatus

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


def require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user(
    user_data: UserCreate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    user = User(
        full_name=user_data.full_name,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        role=user_data.role,
        region=user_data.region,
        is_active=True,
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    return user


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    users = db.scalars(
        select(User).order_by(User.id)
    ).all()

    return users


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user(
    user_id: int,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
def update_user_status(
    user_id: int,
    status_data: UserUpdateStatus,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    user = db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    user.is_active = status_data.is_active
    db.commit()
    db.refresh(user)

    return user