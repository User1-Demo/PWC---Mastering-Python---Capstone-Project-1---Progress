"""
router.py (auth module)

Purpose: Expose the /auth/login endpoint. This reuses the EXACT same
logic we already proved in scripts/test_jwt_login.py - just wrapped
in a FastAPI route now, with proper HTTP error responses instead of
print statements.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.database import get_db
from src.users.models import User
from src.audit.service import log_action
from src.auth.schemas import LoginRequest, TokenResponse, RefreshRequest, UserMeResponse
from src.auth.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from jose import JWTError
from src.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    # Step 1: Look up user by email
    user = db.query(User).filter(User.email == payload.email).first()

    # Step 2: Validate credentials
    # Note: we return the SAME generic error whether the user doesn't exist
    # OR the password is wrong - this prevents attackers from figuring out
    # which emails are registered (a common security practice)
    if not user or not verify_password(payload.password, user.password_hash):
        log_action(
            db,
            actor_id=user.id if user else None,
            action="login_failed",
            entity_type="user",
            entity_id=user.id if user else None,
            metadata={"email_attempted": payload.email},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    # Step 3: Check account is active
    if not user.is_active:
        log_action(
            db,
            actor_id=user.id,
            action="login_blocked_inactive",
            entity_type="user",
            entity_id=user.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    # Step 4: Generate tokens
    access_token = create_access_token(
        user_id=user.id, role=user.role, region=user.region
    )
    refresh_token = create_refresh_token(user_id=user.id)
    log_action(
        db,
        actor_id=user.id,
        action="login_success",
        entity_type="user",
        entity_id=user.id,
    )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
    )

@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    access_token = create_access_token(
        user_id=user.id, role=user.role, region=user.region
    )
    refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        role=user.role,
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    """
    Takes a refresh token, verifies it, and issues a BRAND NEW
    access token + refresh token pair - without requiring the
    password again.
    """
    try:
        decoded = decode_token(payload.refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    if decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type - expected a refresh token",
        )

    user_id = decoded.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists or is deactivated",
        )

    new_access_token = create_access_token(
        user_id=user.id, role=user.role, region=user.region
    )
    new_refresh_token = create_refresh_token(user_id=user.id)

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        role=user.role,
    )


@router.get("/me", response_model=UserMeResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """
    Protected endpoint - requires a valid access token.
    Returns info about whoever's token was sent.
    This proves the FULL authorization chain works end-to-end.
    """
    return current_user