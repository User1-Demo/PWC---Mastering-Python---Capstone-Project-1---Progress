"""
service.py (policies module)

Purpose: Business logic for Policies - separated from the router so
the HTTP layer (router.py) stays thin, and this logic is unit-testable
on its own without needing a running FastAPI app.
"""

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from src.policies.models import Policy
from src.policies.schemas import PolicyCreate


def create_policy(db: Session, payload: PolicyCreate) -> Policy:
    new_policy = Policy(
        policy_number=payload.policy_number,
        type=payload.type.value,
        coverage_amount=payload.coverage_amount,
        region=payload.region,
        status="active",  # new policies always start active
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    db.add(new_policy)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Policy number '{payload.policy_number}' already exists",
        )

    db.refresh(new_policy)
    return new_policy


def get_policy_by_id(db: Session, policy_id: str) -> Policy:
    policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )
    return policy


def list_policies(
    db: Session,
    region: str | None = None,
    status_filter: str | None = None,
    policy_type: str | None = None,
) -> list[Policy]:
    query = db.query(Policy)

    if region:
        query = query.filter(Policy.region == region)
    if status_filter:
        query = query.filter(Policy.status == status_filter)
    if policy_type:
        query = query.filter(Policy.type == policy_type)

    return query.order_by(Policy.created_at.desc()).all()


def update_policy_status(db: Session, policy_id: str, new_status: str) -> Policy:
    policy = get_policy_by_id(db, policy_id)
    policy.status = new_status
    db.commit()
    db.refresh(policy)
    return policy