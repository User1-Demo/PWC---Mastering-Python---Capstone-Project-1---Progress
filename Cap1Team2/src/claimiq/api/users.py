from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from claimiq.core.permissions import require_admin
from claimiq.db.database import get_db
from claimiq.models.user import User
from claimiq.schemas.user import UserCreate, UserResponse, UserUpdate
from claimiq.services.user_service import (
    create_user,
    deactivate_user,
    get_user_by_id,
    get_users,
    update_user,
)

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"],
)


AdminUser = Annotated[User, Depends(require_admin)]


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_user_endpoint(
    user_data: UserCreate,
    db: Annotated[Session, Depends(get_db)],
    _: AdminUser,
) -> User:
    try:
        return create_user(
            db=db,
            user_data=user_data,
            actor_user_id=_.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[UserResponse],
)
def list_users_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: AdminUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[User]:
    return get_users(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
def get_user_endpoint(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: AdminUser,
) -> User:
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}",
    response_model=UserResponse,
)
def update_user_endpoint(
    user_id: int,
    user_data: UserUpdate,
    db: Annotated[Session, Depends(get_db)],
    _: AdminUser,
) -> User:
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    try:
        return update_user(
            db=db,
            user=user,
            user_data=user_data,
            actor_user_id=_.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
)
def deactivate_user_endpoint(
    user_id: int,
    db: Annotated[Session, Depends(get_db)],
    current_user: AdminUser,
) -> User:
    user = get_user_by_id(db, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate themselves",
        )

    return deactivate_user(
        db=db,
        user=user,
        actor_user_id=current_user.id,
    )