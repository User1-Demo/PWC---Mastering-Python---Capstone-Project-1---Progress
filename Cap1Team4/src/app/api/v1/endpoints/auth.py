import hashlib
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token, create_refresh_token, decode_token, verify_password,
)
from app.db.session import get_db
from app.models.user import RefreshToken, User
from app.schemas.auth import LoginRequest, RefreshRequest, TokenPair
from app.services.audit_service import log_action

router = APIRouter(prefix="/auth", tags=["auth"])


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _issue_pair(db: Session, user: User) -> TokenPair:
    refresh = create_refresh_token(user.id)
    db.add(RefreshToken(
        user_id=user.id, token_hash=_hash(refresh),
        expires_at=datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    ))
    return TokenPair(access_token=create_access_token(user.id), refresh_token=refresh)


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)) -> TokenPair:
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    now = datetime.now(UTC)
    locked = user and user.locked_until and user.locked_until.replace(tzinfo=UTC) > now
    ok = bool(user and user.is_active and not locked and verify_password(payload.password, user.hashed_password))
    if not ok:
        if user and not locked:
            user.failed_login_count += 1
            if user.failed_login_count >= settings.LOGIN_MAX_ATTEMPTS:
                user.locked_until = now + timedelta(minutes=settings.LOGIN_LOCK_MINUTES)
        log_action(db, action="LOGIN_FAILED", entity_type="user",
                   entity_id=str(user.id) if user else None, request=request)
        db.commit()
        raise UnauthorizedError("Invalid credentials")  # generic - no user enumeration
    user.failed_login_count = 0
    user.last_login_at = now
    pair = _issue_pair(db, user)
    log_action(db, action="LOGIN_SUCCESS", entity_type="user", entity_id=str(user.id),
               actor=user, request=request)
    db.commit()
    return pair


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        data = decode_token(payload.refresh_token, "refresh")
    except jwt.PyJWTError:
        raise UnauthorizedError() from None
    stored = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.token_hash == _hash(payload.refresh_token))
        .with_for_update()
    )
    if (
        stored is None
        or stored.revoked_at is not None
        or (
            stored.expires_at.replace(tzinfo=UTC)
            if stored.expires_at.tzinfo is None
            else stored.expires_at.astimezone(UTC)
        )
        <= datetime.now(UTC)
    ):
        raise UnauthorizedError()
    user = db.get(User, uuid.UUID(data["sub"]))
    if user is None or not user.is_active:
        raise UnauthorizedError()
    stored.revoked_at = datetime.now(UTC)  # rotate: old refresh token is single-use
    pair = _issue_pair(db, user)
    db.commit()
    return pair
