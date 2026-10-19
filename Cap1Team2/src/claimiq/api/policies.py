from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from claimiq.core.permissions import (
    require_manager_or_admin,
    require_policy_access,
)
from claimiq.db.database import get_db
from claimiq.models.policy import Policy
from claimiq.models.user import User
from claimiq.schemas.policy import (
    PolicyCreate,
    PolicyResponse,
    PolicyUpdate,
)
from claimiq.services.policy_service import (
    create_policy,
    get_policies,
    get_policy_by_id,
    update_policy,
)

router = APIRouter(
    prefix="/api/v1/policies",
    tags=["Policies"],
)


PolicyAccessUser = Annotated[
    User,
    Depends(require_policy_access),
]

ManagerOrAdminUser = Annotated[
    User,
    Depends(require_manager_or_admin),
]


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_policy_endpoint(
    policy_data: PolicyCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: ManagerOrAdminUser,
) -> Policy:
    try:
        return create_policy(
            db=db,
            policy_data=policy_data,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[PolicyResponse],
)
def list_policies_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: PolicyAccessUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=100),
) -> list[Policy]:
    return get_policies(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
)
def get_policy_endpoint(
    policy_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: PolicyAccessUser,
) -> Policy:
    policy = get_policy_by_id(
        db=db,
        policy_id=policy_id,
    )

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    return policy


@router.patch(
    "/{policy_id}",
    response_model=PolicyResponse,
)
def update_policy_endpoint(
    policy_id: int,
    policy_data: PolicyUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: ManagerOrAdminUser,
) -> Policy:
    policy = get_policy_by_id(
        db=db,
        policy_id=policy_id,
    )

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    try:
        return update_policy(
            db=db,
            policy=policy,
            policy_data=policy_data,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc