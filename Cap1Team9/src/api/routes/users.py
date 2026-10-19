from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies.auth import require_roles
from src.common.enums import UserRole
from src.core.security import hash_password
from src.db.session import get_db
from src.models.user import User
from src.schemas.user import UserCreate, UserRead, UserUpdate
from src.services.user_service import *

router = APIRouter(
    prefix="/api/v1/users",
    tags=["users"],
)


@router.post("", response_model=UserRead)
def create_user(
    payload: UserCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    validate_unique_email(payload.email, db)
    validate_unique_username(payload.username, db)

    user = User(
        username=payload.username,
        email=payload.email,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


@router.get("", response_model=list[UserRead])
def list_users(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return get_user_by_id(user_id, db)


@router.put("/{user_id}", response_model=UserRead)
def update_existing_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return update_user(user_id, payload, db)


@router.delete("/{user_id}")
def remove_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return delete_user(user_id, db)
