from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from pwdlib import PasswordHash

from claimiq.core.settings import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """Hash a plain-text password."""
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a password hash."""
    return password_hash.verify(password, hashed_password)


def create_access_token(
    subject: str,
    role: str,
) -> tuple[str, int]:
    """Create a JWT access token."""
    settings = get_settings()
    expires_in = settings.access_token_expire_minutes * 60
    expire = datetime.now(UTC) + timedelta(seconds=expires_in)

    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
    }

    token = jwt.encode(
        payload,
        settings.secret_key,
        algorithm=settings.algorithm,
    )

    return token, expires_in


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT access token."""
    settings = get_settings()

    return jwt.decode(
        token,
        settings.secret_key,
        algorithms=[settings.algorithm],
    )