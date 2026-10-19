import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.db.session import get_db
from app.models.claim import Claim, ClaimNote, ClaimStatusHistory
from app.models.enums import ClaimStatus, UserRole
from app.models.policy import Policy
from app.models.user import User
from app.schemas.claim import (
    ClaimAssignmentUpdate,
    ClaimCreate,
    ClaimOut,
    ClaimNoteOut,
    ClaimStatusHistoryOut,
    ClaimStatusUpdate,
)
from app.services.claim_workflow import change_status, create_claim
from app.services.audit_service import log_action

router = APIRouter(prefix="/claims", tags=["claims"])
claim_submitters = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
)
claim_processors = require_roles(UserRole.ADMIN, UserRole.CLAIMS_MANAGER, UserRole.CLAIMS_ADJUSTER)
claim_managers = require_roles(UserRole.ADMIN, UserRole.CLAIMS_MANAGER)
authenticated = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
    UserRole.SUPPORT_AGENT,
)


@router.post("", response_model=ClaimOut, status_code=201)
def submit_claim(
    payload: ClaimCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(claim_submitters),
) -> Claim:
    return create_claim(db, payload, actor=actor, request=request)


@router.get("", response_model=list[ClaimOut])
def list_claims(
    policy_number: str | None = Query(default=None, max_length=50),
    claimant: str | None = Query(default=None, max_length=150),
    status: ClaimStatus | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=100),
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> list[Claim]:
    query = select(Claim).join(Policy)
    if policy_number:
        query = query.where(Policy.policy_number.ilike(f"%{policy_number}%"))
    if claimant:
        query = query.where(Claim.claimant_name.ilike(f"%{claimant}%"))
    if status:
        query = query.where(Claim.status == status)
    if actor.role == UserRole.CLAIMS_ADJUSTER:
        query = query.where(
            (Claim.region_id == actor.region_id)
            | (Claim.assigned_adjuster_id == actor.id)
        )
    elif actor.role == UserRole.SUPPORT_AGENT:
        query = query.where(Claim.region_id == actor.region_id)
    query = query.order_by(Claim.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    return list(db.scalars(query))


def _visible_claim(claim: Claim, actor: User) -> bool:
    if actor.role == UserRole.CLAIMS_ADJUSTER:
        return claim.region_id == actor.region_id or claim.assigned_adjuster_id == actor.id
    if actor.role == UserRole.SUPPORT_AGENT:
        return claim.region_id == actor.region_id
    return True


@router.get("/{claim_id}", response_model=ClaimOut)
def get_claim(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None or not _visible_claim(claim, actor):
        raise NotFoundError("Claim not found")
    return claim


@router.get("/{claim_id}/history", response_model=list[ClaimStatusHistoryOut])
def get_claim_history(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> list[ClaimStatusHistory]:
    claim = db.get(Claim, claim_id)
    if claim is None or not _visible_claim(claim, actor):
        raise NotFoundError("Claim not found")
    return list(
        db.scalars(
            select(ClaimStatusHistory)
            .where(ClaimStatusHistory.claim_id == claim.id)
            .order_by(ClaimStatusHistory.changed_at.asc())
        )
    )


@router.get("/{claim_id}/notes", response_model=list[ClaimNoteOut])
def get_claim_notes(
    claim_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> list[ClaimNote]:
    claim = db.get(Claim, claim_id)
    if claim is None or not _visible_claim(claim, actor):
        raise NotFoundError("Claim not found")
    return list(
        db.scalars(
            select(ClaimNote)
            .where(ClaimNote.claim_id == claim.id)
            .order_by(ClaimNote.created_at.asc())
        )
    )


@router.patch("/{claim_id}/status", response_model=ClaimOut)
def update_claim_status(
    claim_id: uuid.UUID,
    payload: ClaimStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(claim_processors),
) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise NotFoundError("Claim not found")
    if not _visible_claim(claim, actor):
        raise NotFoundError("Claim not found")
    return change_status(db, claim, payload, actor=actor, request=request)


@router.patch("/{claim_id}/assignment", response_model=ClaimOut)
def assign_claim(
    claim_id: uuid.UUID,
    payload: ClaimAssignmentUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(claim_managers),
) -> Claim:
    claim = db.get(Claim, claim_id)
    if claim is None:
        raise NotFoundError("Claim not found")
    if claim.status == ClaimStatus.CLOSED:
        raise BusinessRuleError("Closed claims cannot be reassigned")
    adjuster = db.get(User, payload.adjuster_id) if payload.adjuster_id else None
    if payload.adjuster_id is not None and (
        adjuster is None
        or not adjuster.is_active
        or adjuster.role != UserRole.CLAIMS_ADJUSTER
        or adjuster.region_id != claim.region_id
    ):
        raise BusinessRuleError("Assigned adjuster must be active and belong to the claim region")
    old_adjuster_id = claim.assigned_adjuster_id
    claim.assigned_adjuster_id = adjuster.id if adjuster else None
    log_action(
        db,
        action="CLAIM_ASSIGNED",
        entity_type="claim",
        entity_id=str(claim.id),
        actor=actor,
        old={"adjuster_id": str(old_adjuster_id) if old_adjuster_id else None},
        new={"adjuster_id": str(claim.assigned_adjuster_id) if claim.assigned_adjuster_id else None},
        request=request,
    )
    db.commit()
    db.refresh(claim)
    return claim
