import pytest
from fastapi import HTTPException

from claimiq.core.permissions import require_roles
from claimiq.models.user import User, UserRole


def create_user(role: UserRole) -> User:
    return User(
        id=1,
        email="user@example.com",
        full_name="Test User",
        password_hash="hashed-password",
        role=role,
        is_active=True,
    )


def test_allowed_role_is_authorized() -> None:
    checker = require_roles(UserRole.ADMIN)
    user = create_user(UserRole.ADMIN)

    result = checker(user)

    assert result is user


def test_disallowed_role_is_rejected() -> None:
    checker = require_roles(UserRole.ADMIN)
    user = create_user(UserRole.SUPPORT_AGENT)

    with pytest.raises(HTTPException) as error:
        checker(user)

    assert error.value.status_code == 403
    assert error.value.detail == "Insufficient permissions"


def test_multiple_roles_are_allowed() -> None:
    checker = require_roles(
        UserRole.ADMIN,
        UserRole.CLAIMS_MANAGER,
    )

    manager = create_user(UserRole.CLAIMS_MANAGER)

    result = checker(manager)

    assert result is manager