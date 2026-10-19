import uuid
import base64
import hashlib
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from cryptography.fernet import Fernet

from app.core.config import settings


def _pii_cipher() -> Fernet:
    key = base64.urlsafe_b64encode(
        hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    )
    return Fernet(key)


def encrypt_sensitive_value(value: str) -> str:
    return _pii_cipher().encrypt(value.encode()).decode()


def decrypt_sensitive_value(value: str) -> str:
    return _pii_cipher().decrypt(value.encode()).decode()


def hash_password(password: str) -> str:
    password_digest = hashlib.sha256(password.encode()).digest()
    return "sha256+bcrypt$" + bcrypt.hashpw(
        password_digest, bcrypt.gensalt()
    ).decode()


def verify_password(password: str, hashed: str) -> bool:
    try:
        if hashed.startswith("sha256+bcrypt$"):
            password_digest = hashlib.sha256(password.encode()).digest()
            return bcrypt.checkpw(
                password_digest, hashed.removeprefix("sha256+bcrypt$").encode()
            )
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except ValueError:
        return False


def _create_token(subject: str, token_type: str, expires: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": now,
        "exp": now + expires,
        "jti": uuid.uuid4().hex,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: uuid.UUID) -> str:
    return _create_token(
        str(user_id), "access", timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(user_id: uuid.UUID) -> str:
    return _create_token(
        str(user_id), "refresh", timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, expected_type: str) -> dict[str, Any]:
    """Raises jwt.PyJWTError on any problem (expired, bad signature, wrong type)."""
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    if payload.get("type") != expected_type:
        raise jwt.InvalidTokenError("wrong token type")
    return payload
