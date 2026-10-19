from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.claim import Claim
from claimiq.models.policy import Policy
from claimiq.schemas.claim import ClaimCreate, ClaimUpdate
from claimiq.services.audit_service import create_audit_log


def get_claim_by_id(
    db: Session,
    claim_id: int,
) -> Claim | None:
    return db.get(Claim, claim_id)


def get_claim_by_number(
    db: Session,
    claim_number: str,
) -> Claim | None:
    statement = select(Claim).where(
        Claim.claim_number == claim_number,
    )
    return db.scalar(statement)


def get_claims(
    db: Session,
    skip: int = 0,
    limit: int = 100,
) -> list[Claim]:
    statement = (
        select(Claim)
        .order_by(Claim.id)
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def create_claim(
    db: Session,
    claim_data: ClaimCreate,
    actor_user_id: int | None = None,
) -> Claim:
    existing_claim = get_claim_by_number(
        db,
        claim_data.claim_number,
    )

    if existing_claim is not None:
        raise ValueError("A claim with this number already exists")

    policy = db.get(Policy, claim_data.policy_id)

    if policy is None:
        raise ValueError("The selected policy does not exist")

    claim = Claim(
        **claim_data.model_dump(),
    )

    db.add(claim)
    db.commit()
    db.refresh(claim)

    create_audit_log(
        db=db,
        action="CLAIM_CREATED",
        user_id=actor_user_id,
        entity_type="Claim",
        entity_id=claim.id,
        metadata={
            "claim_number": claim.claim_number,
            "policy_id": claim.policy_id,
        },
    )

    return claim


def update_claim(
    db: Session,
    claim: Claim,
    claim_data: ClaimUpdate,
    actor_user_id: int | None = None,
) -> Claim:
    update_data = claim_data.model_dump(exclude_unset=True)

    if "policy_id" in update_data:
        policy = db.get(Policy, update_data["policy_id"])

        if policy is None:
            raise ValueError("The selected policy does not exist")

    for field, value in update_data.items():
        setattr(claim, field, value)

    db.commit()
    db.refresh(claim)

    create_audit_log(
        db=db,
        action="CLAIM_UPDATED",
        user_id=actor_user_id,
        entity_type="Claim",
        entity_id=claim.id,
        metadata={
            "updated_fields": list(update_data.keys()),
        },
    )
    return claim