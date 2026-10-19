from claimiq.core.security import hash_password, verify_password


def test_password_is_hashed() -> None:
    password = "SecurePassword123"

    hashed_password = hash_password(password)

    assert hashed_password != password
    assert hashed_password


def test_correct_password_is_verified() -> None:
    password = "SecurePassword123"
    hashed_password = hash_password(password)

    assert verify_password(password, hashed_password) is True


def test_incorrect_password_is_rejected() -> None:
    password = "SecurePassword123"
    hashed_password = hash_password(password)

    assert verify_password("WrongPassword123", hashed_password) is False


def test_same_password_generates_different_hashes() -> None:
    password = "SecurePassword123"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash

import jwt
import pytest

from claimiq.core.security import (
    create_access_token,
    decode_access_token,
)


def test_access_token_contains_subject_and_role() -> None:
    token, expires_in = create_access_token(
        subject="1",
        role="CLAIMS_ADJUSTER",
    )

    payload = decode_access_token(token)

    assert payload["sub"] == "1"
    assert payload["role"] == "CLAIMS_ADJUSTER"
    assert expires_in > 0


def test_invalid_token_is_rejected() -> None:
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("invalid.jwt.token")