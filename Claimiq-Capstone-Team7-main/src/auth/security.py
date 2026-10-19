"""
security.py (auth module)

Purpose: Centralize two things every module will need:
1. Password hashing/verification (using argon2 - already proven in our scripts)
2. JWT token creation/verification

This becomes the ONE place that knows how to create and check tokens -
no other file should duplicate this logic.
"""

import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from jose import jwt, JWTError

load_dotenv()

# ---------------------------------------------------------
# Password hashing setup (same as our earlier proven script)
# ---------------------------------------------------------
ph = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Convert a plain password into an argon2 hash."""
    return ph.hash(plain_password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Check if a plain password matches a stored hash.
    Returns True if it matches, False if it doesn't.
    """
    try:
        ph.verify(password_hash, plain_password)
        return True
    except VerifyMismatchError:
        return False


# ---------------------------------------------------------
# JWT settings (loaded from .env)
# ---------------------------------------------------------
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 15))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))


def create_access_token(user_id: str, role: str, region: str | None = None) -> str:
    """
    Create a short-lived JWT access token.

    The 'payload' (data inside the token) includes:
    - sub (subject) = the user's id -> standard JWT convention
    - role = so we can check permissions without hitting the DB every time
    - region = for row-level scoping (BR-004 from our SRS)
    - exp = expiry timestamp -> after this, the token is automatically invalid
    - type = "access" -> distinguishes this from a refresh token
    """
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    payload = {
        "sub": str(user_id),
        "role": role,
        "region": region,
        "exp": expire,
        "type": "access",
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def create_refresh_token(user_id: str) -> str:
    """
    Create a long-lived JWT refresh token.
    Notice: refresh tokens carry MINIMAL data (just the user id) -
    they're only used to get a NEW access token, not for authorization checks directly.
    """
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }

    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    """
    Verify a token's signature and expiry, and return its payload.
    Raises JWTError if the token is invalid, tampered, or expired.
    """
    payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    return payload