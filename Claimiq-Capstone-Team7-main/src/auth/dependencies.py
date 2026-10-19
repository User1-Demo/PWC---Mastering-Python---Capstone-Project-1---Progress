"""
dependencies.py (auth module)

Purpose: Reusable FastAPI dependencies for protecting endpoints.

- get_current_user(): decodes the JWT from the Authorization header,
  fetches the matching user from the database, and returns it.
  Any endpoint can require this if it just needs "someone logged in."

- require_role([...]): wraps get_current_user() and additionally checks
  that the user's role is in an allowed list. Use this for Admin-only,
  Manager-only, etc. endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from src.database import get_db
from src.users.models import User
from src.auth.security import decode_token

# This gives Swagger's "Authorize" button a SIMPLE paste-your-token box,
# instead of a full username/password/client_id OAuth2 login form.
# We don't use OAuth2PasswordBearer because our /auth/login endpoint
# accepts JSON, not OAuth2's form-encoded username/password format.
bearer_scheme = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Runs on every protected endpoint:
    1. Extracts the JWT from the 'Authorization: Bearer <token>' header
       (HTTPBearer does this extraction automatically into 'credentials')
    2. Decodes/verifies it (signature + expiry check)
    3. Looks up the matching user in the database
    4. Returns the User object - endpoints can then use it directly
    """
    token = credentials.credentials  # the raw token string, after "Bearer "

    try:
        payload = decode_token(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Make sure this is an ACCESS token, not a refresh token being misused here
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
        )

    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated",
        )

    return user


def require_role(allowed_roles: list[str]):
    """
    Factory function - returns a dependency that checks role membership.

    Usage on an endpoint:
        @router.post("/documents", dependencies=[Depends(require_role(["admin"]))])

    or to also GET the user object:
        def upload_doc(current_user: User = Depends(require_role(["admin"]))):
    """

    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )
        return current_user

    return role_checker