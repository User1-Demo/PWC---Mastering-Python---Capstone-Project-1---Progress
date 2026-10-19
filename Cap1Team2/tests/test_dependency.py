from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from claimiq.core.dependencies import get_current_user
from claimiq.core.security import create_access_token
from claimiq.models.user import User, UserRole


def test_get_current_user_returns_active_user() -> None:
    user = User(
        id=1,
        email="adjuster@example.com",
        full_name="Test Adjuster",
        password_hash="hashed-password",
        role=UserRole.CLAIMS_ADJUSTER,
        is_active=True,
    )

    token, _ = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    db = Mock()
    db.get.return_value = user

    result = get_current_user(token=token, db=db)

    assert result is user
    db.get.assert_called_once_with(User, 1)


def test_get_current_user_rejects_invalid_token() -> None:
    db = Mock()

    with pytest.raises(HTTPException) as error:
        get_current_user(
            token="invalid-token",
            db=db,
        )

    assert error.value.status_code == 401
    db.get.assert_not_called()


def test_get_current_user_rejects_inactive_user() -> None:
    user = User(
        id=1,
        email="inactive@example.com",
        full_name="Inactive User",
        password_hash="hashed-password",
        role=UserRole.CLAIMS_ADJUSTER,
        is_active=False,
    )

    token, _ = create_access_token(
        subject=str(user.id),
        role=user.role.value,
    )

    db = Mock()
    db.get.return_value = user

    with pytest.raises(HTTPException) as error:
        get_current_user(token=token, db=db)

    assert error.value.status_code == 401