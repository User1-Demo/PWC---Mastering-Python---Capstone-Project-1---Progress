import pytest
from pydantic import ValidationError

from claimiq.models.user import UserRole
from claimiq.schemas.user import UserCreate


def test_valid_user_schema() -> None:
    user = UserCreate(
        email="adjuster@example.com",
        full_name="Test Adjuster",
        password="SecurePassword123",
        role=UserRole.CLAIMS_ADJUSTER,
    )

    assert user.email == "adjuster@example.com"
    assert user.role == UserRole.CLAIMS_ADJUSTER


def test_invalid_email_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="not-an-email",
            full_name="Test User",
            password="SecurePassword123",
        )


def test_short_password_is_rejected() -> None:
    with pytest.raises(ValidationError):
        UserCreate(
            email="user@example.com",
            full_name="Test User",
            password="short",
        )