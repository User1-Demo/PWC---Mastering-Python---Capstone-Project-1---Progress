from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.core.security import verify_password
from claimiq.models.user import User


def authenticate_user(
    db: Session,
    email: str,
    password: str,
) -> User | None:
    """Authenticate a user by email and password."""

    statement = select(User).where(User.email == email)
    user = db.scalar(statement)

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(password, user.password_hash):
        return None

    return user