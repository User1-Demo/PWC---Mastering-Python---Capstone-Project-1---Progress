from collections.abc import Callable

from fastapi import HTTPException, status

from claimiq.core.dependencies import CurrentUser
from claimiq.models.user import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable:
    """
    Allow access only to users with one of the specified roles.
    """

    def role_checker(current_user: CurrentUser) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker


require_admin = require_roles(UserRole.ADMIN)

require_manager_or_admin = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
)

require_claims_staff = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
)

require_policy_access = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
    UserRole.SUPPORT_AGENT,
)