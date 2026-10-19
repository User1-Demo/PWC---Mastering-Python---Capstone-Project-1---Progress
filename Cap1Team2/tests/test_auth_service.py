from unittest.mock import Mock

from claimiq.core.security import hash_password
from claimiq.models.user import User, UserRole
from claimiq.services.auth_service import authenticate_user


def create_test_user(
    *,
    is_active: bool = True,
) -> User:
    return User(
        id=1,
        email="admin@example.com",
        full_name="Test Admin",
        password_hash=hash_password("SecurePassword123"),
        role=UserRole.ADMIN,
        is_active=is_active,
    )


def test_authenticate_user_with_valid_credentials() -> None:
    user = create_test_user()

    db = Mock()
    db.scalar.return_value = user

    result = authenticate_user(
        db=db,
        email="admin@example.com",
        password="SecurePassword123",
    )

    assert result is user


def test_authenticate_user_with_wrong_password() -> None:
    user = create_test_user()

    db = Mock()
    db.scalar.return_value = user

    result = authenticate_user(
        db=db,
        email="admin@example.com",
        password="WrongPassword123",
    )

    assert result is None


def test_authenticate_user_with_unknown_email() -> None:
    db = Mock()
    db.scalar.return_value = None

    result = authenticate_user(
        db=db,
        email="unknown@example.com",
        password="SecurePassword123",
    )

    assert result is None


def test_inactive_user_cannot_authenticate() -> None:
    user = create_test_user(is_active=False)

    db = Mock()
    db.scalar.return_value = user

    result = authenticate_user(
        db=db,
        email="admin@example.com",
        password="SecurePassword123",
    )

    assert result is None