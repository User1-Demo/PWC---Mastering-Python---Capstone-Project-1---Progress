from sqlalchemy.orm import Session

from src.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from src.models.user import User


def authenticate_user(
    email: str,
    password: str,
    db: Session,
) -> User | None:
    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    if not user.is_active:
        return None

    return user


def create_tokens(user: User) -> dict[str, str]:
    access_token = create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )

    refresh_token = create_refresh_token(
        user_id=user.id,
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


def refresh_access_token(
    refresh_token: str,
    db: Session,
) -> str:
    payload = decode_token(refresh_token)

    if payload.get("type") != "refresh":
        raise ValueError("Invalid token type")

    user_id = payload.get("sub")

    if not user_id:
        raise ValueError("Invalid refresh token")

    user = db.query(User).filter(User.id == int(user_id)).first()

    if not user:
        raise ValueError("User not found")

    if not user.is_active:
        raise ValueError("User is inactive")

    return create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role,
    )
