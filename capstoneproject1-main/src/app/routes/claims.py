from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from src.app.schemas.note import ClaimNoteCreate
from src.app.core.security import get_current_user
from src.app.db.models import (
    Claim,
    ClaimNote,
    ClaimStatus,
    Policy,
    PolicyStatus,
    User,
    UserRole,
)
from src.app.db.session import get_db
from src.app.schemas.claim import (
    ClaimCreate,
    ClaimDetailResponse,
    ClaimResponse,
    ClaimStatusUpdate,
)
from src.app.services.audit import create_audit_log

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claims"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


ALLOWED_TRANSITIONS = {
    ClaimStatus.SUBMITTED: [ClaimStatus.UNDER_REVIEW],
    ClaimStatus.UNDER_REVIEW: [ClaimStatus.APPROVED, ClaimStatus.REJECTED],
    ClaimStatus.APPROVED: [ClaimStatus.CLOSED],
    ClaimStatus.REJECTED: [ClaimStatus.CLOSED],
    ClaimStatus.CLOSED: [],
}


def can_view_claim(current_user: User, claim: Claim) -> bool:
    if current_user.role in [UserRole.ADMIN, UserRole.CLAIMS_MANAGER]:
        return True

    if current_user.role == UserRole.CLAIMS_ADJUSTER:
        return (
            claim.assigned_adjuster_id == current_user.id
            or claim.region == current_user.region
        )

    if current_user.role == UserRole.SUPPORT_AGENT:
        return claim.region == current_user.region

    return False


def can_update_claim(current_user: User, claim: Claim) -> bool:
    if current_user.role in [UserRole.ADMIN, UserRole.CLAIMS_MANAGER]:
        return True

    if current_user.role == UserRole.CLAIMS_ADJUSTER:
        return (
            claim.assigned_adjuster_id == current_user.id
            or claim.region == current_user.region
        )

    return False


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_claim(
    claim_data: ClaimCreate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in [
        UserRole.ADMIN,
        UserRole.CLAIMS_MANAGER,
        UserRole.CLAIMS_ADJUSTER,
        UserRole.SUPPORT_AGENT,
    ]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create claims",
        )

    policy = db.get(Policy, claim_data.policy_id)

    if policy is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Policy not found",
        )

    if policy.status != PolicyStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim must be linked to an active policy",
        )

    if not (
        policy.coverage_start
        <= claim_data.incident_date
        <= policy.coverage_end
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incident date is outside the policy coverage period",
        )

    if claim_data.claim_type != policy.policy_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Claim type must match the policy type",
        )

    if current_user.role in [UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT]:
        if current_user.region and claim_data.region != current_user.region:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create claim outside your region",
            )

    claim = Claim(
        claim_number=claim_data.claim_number,
        policy_id=claim_data.policy_id,
        claimant_name=claim_data.claimant_name,
        claim_type=claim_data.claim_type,
        region=claim_data.region,
        amount=claim_data.amount,
        description=claim_data.description,
        incident_date=claim_data.incident_date,
        status=ClaimStatus.SUBMITTED,
    )

    db.add(claim)

    try:
        db.commit()
        db.refresh(claim)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A claim with this claim number already exists",
        )

    create_audit_log(
        db,
        user_id=current_user.id,
        action="CLAIM_CREATED",
        entity_type="claim",
        entity_id=claim.id,
        details=f"Claim {claim.claim_number} created with status {claim.status.value}",
    )
    db.commit()

    return claim


@router.patch(
    "/{claim_id}/status",
    response_model=ClaimResponse,
)
def update_claim_status(
    claim_id: int,
    status_data: ClaimStatusUpdate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    if not can_update_claim(current_user, claim):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this claim",
        )

    if current_user.role == UserRole.SUPPORT_AGENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Support agents cannot update claim status",
        )

    previous_status = claim.status
    allowed_statuses = ALLOWED_TRANSITIONS.get(claim.status, [])

    is_override_allowed = (
        current_user.role in [UserRole.ADMIN, UserRole.CLAIMS_MANAGER]
        and status_data.manager_override
        and status_data.override_reason
    )

    if status_data.status not in allowed_statuses and not is_override_allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Invalid transition "
                f"from {claim.status.value} "
                f"to {status_data.status.value}"
            ),
        )

    claim.status = status_data.status

    if status_data.status == ClaimStatus.CLOSED:
        claim.closed_at = datetime.utcnow()

    if status_data.note:
        note = ClaimNote(
            claim_id=claim.id,
            user_id=current_user.id,
            note=status_data.note,
        )
        db.add(note)

    if is_override_allowed:
        override_note = ClaimNote(
            claim_id=claim.id,
            user_id=current_user.id,
            note=f"Manager override reason: {status_data.override_reason}",
        )
        db.add(override_note)

    create_audit_log(
        db,
        user_id=current_user.id,
        action="CLAIM_STATUS_UPDATED",
        entity_type="claim",
        entity_id=claim.id,
        details=(
            f"Claim {claim.claim_number} status changed "
            f"from {previous_status.value} to {claim.status.value}"
        ),
    )

    if is_override_allowed:
        create_audit_log(
            db,
            user_id=current_user.id,
            action="CLAIM_STATUS_OVERRIDE",
            entity_type="claim",
            entity_id=claim.id,
            details=(
                f"Override from {previous_status.value} to {claim.status.value}. "
                f"Reason: {status_data.override_reason}"
            ),
        )

    db.commit()
    db.refresh(claim)

    return claim


@router.post(
    "/{claim_id}/notes",
    response_model=ClaimDetailResponse,
)
@router.post(
    "/{claim_id}/notes",
    response_model=ClaimDetailResponse,
)
def add_claim_note(
    claim_id: int,
    payload: ClaimNoteCreate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    claim = db.execute(
        select(Claim)
        .options(selectinload(Claim.notes))
        .where(Claim.id == claim_id)
    ).scalar_one_or_none()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    if not can_update_claim(current_user, claim):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add notes to this claim",
        )

    note = ClaimNote(
        claim_id=claim.id,
        user_id=current_user.id,
        note=payload.note,
    )
    db.add(note)

    create_audit_log(
        db,
        user_id=current_user.id,
        action="CLAIM_NOTE_ADDED",
        entity_type="claim",
        entity_id=claim.id,
        details=f"Note added to claim {claim.claim_number}",
    )

    db.commit()

    claim = db.execute(
        select(Claim)
        .options(selectinload(Claim.notes))
        .where(Claim.id == claim_id)
    ).scalar_one()

    return claim


@router.get(
    "",
    response_model=list[ClaimResponse],
)
def list_claims(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
    claim_number: str | None = Query(default=None),
    claimant_name: str | None = Query(default=None),
    claim_status: ClaimStatus | None = Query(default=None),
    policy_number: str | None = Query(default=None),
):
    query = select(Claim).join(Policy).order_by(Claim.id)

    if current_user.role in [UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT]:
        if current_user.region:
            query = query.where(Claim.region == current_user.region)

    if claim_number:
        query = query.where(
            Claim.claim_number.ilike(f"%{claim_number}%")
        )

    if claimant_name:
        query = query.where(
            Claim.claimant_name.ilike(f"%{claimant_name}%")
        )

    if claim_status:
        query = query.where(Claim.status == claim_status)

    if policy_number:
        query = query.where(
            Policy.policy_number.ilike(f"%{policy_number}%")
        )

    return db.scalars(query).all()


@router.get(
    "/{claim_id}",
    response_model=ClaimDetailResponse,
)
def get_claim(
    claim_id: int,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    claim = db.execute(
        select(Claim)
        .options(selectinload(Claim.notes))
        .where(Claim.id == claim_id)
    ).scalar_one_or_none()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    if not can_view_claim(current_user, claim):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this claim",
        )

    return claim