from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.core.security import hash_password
from claimiq.models.user import User
from claimiq.schemas.user import UserCreate, UserUpdate
from claimiq.services.audit_service import create_audit_log


def get_user_by_id(
    db: Session,
    user_id: int,
) -> User | None:
    return db.get(User, user_id)


def get_user_by_email(
    db: Session,
    email: str,
) -> User | None:
    statement = select(User).where(User.email == email.lower())
    return db.scalar(statement)


def get_users(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[User]:
    statement = (
        select(User)
        .order_by(User.id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def create_user(
    db: Session,
    user_data: UserCreate,
    actor_user_id: int | None = None,
) -> User:
    normalized_email = str(user_data.email).lower()

    existing_user = get_user_by_email(db, normalized_email)

    if existing_user is not None:
        raise ValueError("A user with this email already exists")

    user = User(
        email=normalized_email,
        full_name=user_data.full_name,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        action="USER_CREATED",
        user_id=actor_user_id,
        entity_type="User",
        entity_id=user.id,
        metadata={
            "email": user.email,
            "role": user.role.value,
        },
    )

    return user


def update_user(
    db: Session,
    user: User,
    user_data: UserUpdate,
    actor_user_id: int | None = None,
) -> User:
    update_data = user_data.model_dump(exclude_unset=True)

    if "email" in update_data and update_data["email"] is not None:
        normalized_email = str(update_data["email"]).lower()

        existing_user = get_user_by_email(db, normalized_email)

        if existing_user is not None and existing_user.id != user.id:
            raise ValueError("A user with this email already exists")

        update_data["email"] = normalized_email

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        action="USER_UPDATED",
        user_id=actor_user_id,
        entity_type="User",
        entity_id=user.id,
        metadata={
            "updated_fields": list(update_data.keys()),
        },
    )

    return user


def deactivate_user(
    db: Session,
    user: User,
    actor_user_id: int | None = None,
) -> User:
    user.is_active = False

    db.commit()
    db.refresh(user)

    create_audit_log(
        db=db,
        action="USER_DEACTIVATED",
        user_id=actor_user_id,
        entity_type="User",
        entity_id=user.id,
        metadata=None,
    )

    return user