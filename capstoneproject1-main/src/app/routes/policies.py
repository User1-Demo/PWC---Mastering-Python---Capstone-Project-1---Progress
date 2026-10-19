from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from src.app.core.security import get_current_user
from src.app.db.models import Policy, User, UserRole
from src.app.db.session import get_db
from src.app.schemas.policy import PolicyCreate, PolicyResponse

router = APIRouter(
    prefix="/api/v1/policies",
    tags=["Policies"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=PolicyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_policy(
    policy_data: PolicyCreate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can create policies",
        )

    policy = Policy(
        policy_number=policy_data.policy_number,
        policy_type=policy_data.policy_type,
        holder_name=policy_data.holder_name,
        region=policy_data.region,
        coverage_start=policy_data.coverage_start,
        coverage_end=policy_data.coverage_end,
        status=policy_data.status,
    )

    db.add(policy)

    try:
        db.commit()
        db.refresh(policy)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A policy with this policy number already exists",
        )

    return policy


@router.get(
    "",
    response_model=list[PolicyResponse],
)
def list_policies(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
    policy_number: str | None = Query(
        default=None,
        min_length=1,
    ),
):
    query = select(Policy).order_by(Policy.id)

    if current_user.role in [UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT]:
        if current_user.region:
            query = query.where(Policy.region == current_user.region)

    if policy_number:
        query = query.where(
            Policy.policy_number.ilike(f"%{policy_number}%")
        )

    return db.scalars(query).all()


@router.get(
    "/{policy_id}",
    response_model=PolicyResponse,
)
def get_policy(
    policy_id: int,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    policy = db.get(Policy, policy_id)

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    if current_user.role in [UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT]:
        if current_user.region and policy.region != current_user.region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view this policy",
            )

    return policy