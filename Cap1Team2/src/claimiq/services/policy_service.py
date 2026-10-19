from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.policy import Policy
from claimiq.schemas.policy import PolicyCreate, PolicyUpdate
from claimiq.services.audit_service import create_audit_log


def get_policy_by_id(
    db: Session,
    policy_id: int,
) -> Policy | None:
    return db.get(Policy, policy_id)


def get_policy_by_number(
    db: Session,
    policy_number: str,
) -> Policy | None:
    statement = select(Policy).where(
        Policy.policy_number == policy_number
    )
    return db.scalar(statement)


def get_policies(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Policy]:
    statement = (
        select(Policy)
        .order_by(Policy.id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def create_policy(
    db: Session,
    policy_data: PolicyCreate,
    actor_user_id: int | None = None,
) -> Policy:
    existing_policy = get_policy_by_number(
        db,
        policy_data.policy_number,
    )

    if existing_policy is not None:
        raise ValueError("A policy with this number already exists")

    if policy_data.end_date < policy_data.start_date:
        raise ValueError(
            "Policy end date cannot be before the start date"
        )

    policy = Policy(
        **policy_data.model_dump(),
    )

    db.add(policy)
    db.commit()
    db.refresh(policy)

    create_audit_log(
        db=db,
        action="POLICY_CREATED",
        user_id=actor_user_id,
        entity_type="Policy",
        entity_id=policy.id
    )

    return policy


def update_policy(
    db: Session,
    policy: Policy,
    policy_data: PolicyUpdate,
    actor_user_id: int | None = None,
) -> Policy:
    update_data = policy_data.model_dump(exclude_unset=True)

    start_date = update_data.get("start_date", policy.start_date)
    end_date = update_data.get("end_date", policy.end_date)

    if end_date < start_date:
        raise ValueError(
            "Policy end date cannot be before the start date"
        )

    for field, value in update_data.items():
        setattr(policy, field, value)

    db.commit()
    db.refresh(policy)

    create_audit_log(
        db=db,
        action="POLICY_UPDATED",
        user_id=actor_user_id,
        entity_type="Policy",
        entity_id=policy.id,
        metadata={
            "updated_fields": list(update_data.keys()),
        },
    )

    return policy