from datetime import datetime

from fastapi import HTTPException

from src.common.enums import PolicyStatus
from src.models.policy import Policy


def generate_policy_number(db):

    year = datetime.now().year

    latest_policy = db.query(Policy).order_by(Policy.id.desc()).first()

    if not latest_policy:
        sequence = 1

    else:
        last_number = latest_policy.policy_number

        sequence = int(last_number.split("-")[-1]) + 1

    return f"POL-{year}-{sequence:06d}"


def create_policy(payload, db):

    policy = Policy(
        policy_number=generate_policy_number(db),
        customer_id=payload.customer_id,
        policy_type=payload.policy_type,
        coverage_limit=payload.coverage_limit,
        region=payload.region,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )

    db.add(policy)

    db.commit()

    db.refresh(policy)

    return policy


def get_policies(db):
    return db.query(Policy).all()


def get_policy_by_id(policy_id: int, db):

    policy = db.query(Policy).filter(Policy.id == policy_id).first()

    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found")

    return policy


def update_policy(policy_id: int, payload, db):

    policy = get_policy_by_id(policy_id, db)

    if payload.policy_type:
        policy.policy_type = payload.policy_type

    if payload.coverage_limit:
        policy.coverage_limit = payload.coverage_limit

    if payload.region:
        policy.region = payload.region

    if payload.start_date:
        policy.start_date = payload.start_date

    if payload.end_date:
        policy.end_date = payload.end_date

    if payload.status:
        policy.status = payload.status

    db.commit()

    db.refresh(policy)

    return policy


def delete_policy(policy_id: int, db):

    policy = get_policy_by_id(policy_id, db)

    policy.status = PolicyStatus.inactive

    db.commit()
    db.refresh(policy)

    return {"message": "Policy deactivated successfully"}
