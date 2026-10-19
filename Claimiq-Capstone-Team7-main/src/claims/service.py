"""
service.py (claims module)

Purpose: Business logic for Claims - the biggest module. Handles
creation (with policy validation), role-scoped querying (BR-004),
and status transitions (delegating rules to workflow.py).
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from sqlalchemy import or_
from fastapi import HTTPException, status

from src.claims.models import Claim, ClaimNote, ClaimStatusHistory
from src.policies.models import Policy
from src.users.models import User
from src.claims.schemas import ClaimCreate, ClaimStatusUpdate
from src.claims import workflow
from src.audit.service import log_action

# FR-015: SLA should be configurable. Hardcoded for now - move to
# a settings/config value later (e.g., per claim_type or region).
SLA_DAYS = 7


def generate_claim_number(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(Claim).count() + 1
    return f"CLM-{year}-{count:06d}"


def create_claim(db: Session, payload: ClaimCreate, current_user: User) -> Claim:
    # BR-002: claim must be linked to a valid, ACTIVE policy
    policy = db.query(Policy).filter(Policy.id == payload.policy_id).first()
    if not policy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found"
        )
    if policy.status != "active":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Cannot create a claim against an inactive policy",
        )

    # Data integrity check: claim_type should match the policy's own type
    if payload.claim_type.value != policy.type:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"claim_type '{payload.claim_type.value}' does not match "
                f"policy type '{policy.type}'"
            ),
        )

    claim_number = generate_claim_number(db)
    now = datetime.now(timezone.utc)

    new_claim = Claim(
        claim_number=claim_number,
        policy_id=policy.id,
        claimant_name=payload.claimant_name,
        claim_type=payload.claim_type.value,
        region=policy.region,  # inherited from the policy, not user-supplied
        amount_claimed=payload.amount_claimed,
        status="submitted",
        sla_due_at=now + timedelta(days=SLA_DAYS),
    )

    db.add(new_claim)
    db.commit()
    db.refresh(new_claim)

    # BR-007: append-only history - record the very first state too
    history_entry = ClaimStatusHistory(
        claim_id=new_claim.id,
        from_status=None,
        to_status="submitted",
        changed_by=current_user.id,
    )
    db.add(history_entry)
    db.commit()
    log_action(
        db,
        actor_id=current_user.id,
        action="claim_created",
        entity_type="claim",
        entity_id=new_claim.id,
        metadata={"claim_number": new_claim.claim_number, "status": "submitted"},
    )

    return new_claim


def _scope_query_to_role(query, current_user: User):
    """
    BR-004: Adjusters see only claims assigned to them OR in their
    region. Admin/Manager/Support Agent see everything (Support
    Agents need full visibility to answer customer status queries,
    per FR-006).
    """
    if current_user.role == "adjuster":
        query = query.filter(
            or_(
                Claim.assigned_adjuster_id == current_user.id,
                Claim.region == current_user.region,
            )
        )
    return query


def get_claim_by_id(db: Session, claim_id: str, current_user: User) -> Claim:
    query = db.query(Claim).filter(Claim.id == claim_id)
    query = _scope_query_to_role(query, current_user)
    claim = query.first()
    if not claim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Claim not found"
        )
    return claim


def list_claims(
    db: Session,
    current_user: User,
    policy_number: str | None = None,
    claimant_name: str | None = None,
    status_filter: str | None = None,
) -> list[Claim]:
    query = db.query(Claim)
    query = _scope_query_to_role(query, current_user)

    if policy_number:
        query = query.join(Policy).filter(Policy.policy_number == policy_number)
    if claimant_name:
        query = query.filter(Claim.claimant_name.ilike(f"%{claimant_name}%"))
    if status_filter:
        query = query.filter(Claim.status == status_filter)

    return query.order_by(Claim.submitted_at.desc()).all()


def update_claim_status(
    db: Session,
    claim_id: str,
    payload: ClaimStatusUpdate,
    current_user: User,
) -> Claim:
    claim = get_claim_by_id(db, claim_id, current_user)

    # BR-003: only a Manager may use the override path
    if payload.override_flag and current_user.role != "manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only a Manager can override the claim status workflow",
        )

    try:
        workflow.validate_transition(
            from_status=claim.status,
            to_status=payload.to_status.value,
            override_flag=payload.override_flag,
            override_justification=payload.override_justification,
        )
    except workflow.OverrideJustificationRequiredError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )
    except workflow.InvalidTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)
        )

    previous_status = claim.status
    claim.status = payload.to_status.value

    if payload.assigned_adjuster_id:
        claim.assigned_adjuster_id = payload.assigned_adjuster_id

    if payload.override_flag:
        claim.override_flag = True
        claim.override_justification = payload.override_justification

    db.commit()
    
    db.refresh(claim)

    # BR-007: append-only history entry for this transition
    history_entry = ClaimStatusHistory(
        claim_id=claim.id,
        from_status=previous_status,
        to_status=claim.status,
        changed_by=current_user.id,
    )
    db.add(history_entry)

    if payload.note:
        note = ClaimNote(
            claim_id=claim.id,
            author_id=current_user.id,
            note_text=payload.note,
        )
        db.add(note)
    log_action(
        db,
        actor_id=current_user.id,
        action="claim_status_changed",
        entity_type="claim",
        entity_id=claim.id,
        metadata={
            "from_status": previous_status,
            "to_status": claim.status,
            "override_flag": payload.override_flag,
        },
    )
    db.commit()
    db.refresh(claim)

    return claim


def list_claim_notes(db: Session, claim_id: str, current_user: User) -> list[ClaimNote]:
    # Reuses role scoping - confirms this user is even allowed to see the claim first
    get_claim_by_id(db, claim_id, current_user)
    return (
        db.query(ClaimNote)
        .filter(ClaimNote.claim_id == claim_id)
        .order_by(ClaimNote.created_at.asc())
        .all()
    )