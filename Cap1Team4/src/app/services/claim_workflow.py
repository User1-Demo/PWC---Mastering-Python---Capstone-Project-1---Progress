import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.core.security import encrypt_sensitive_value
from app.models.claim import Claim, ClaimNote, ClaimStatusHistory
from app.models.enums import ClaimStatus, NoteType, PolicyStatus, UserRole
from app.models.policy import Policy
from app.models.user import User
from app.schemas.claim import ClaimCreate, ClaimStatusUpdate
from app.services.audit_service import log_action


def _enum_value(value) -> str:
    return value.value if hasattr(value, "value") else str(value)


def create_claim(
    db: Session,
    payload: ClaimCreate,
    *,
    actor: User,
    request: Request | None = None,
) -> Claim:
    policy = db.get(Policy, payload.policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    if policy.status != PolicyStatus.ACTIVE:
        raise BusinessRuleError("Claims can only be submitted against an active policy")
    if (
        actor.role in (UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT)
        and actor.region_id != policy.region_id
    ):
        raise NotFoundError("Policy not found")
    if payload.claim_type != policy.policy_type:
        raise BusinessRuleError("Claim type must match the policy type")
    if not policy.start_date <= payload.incident_date <= policy.end_date:
        raise BusinessRuleError("Incident date must fall within the policy coverage period")
    if payload.assigned_adjuster_id is not None:
        adjuster = db.get(User, payload.assigned_adjuster_id)
        if (
            adjuster is None
            or not adjuster.is_active
            or adjuster.role != UserRole.CLAIMS_ADJUSTER
            or adjuster.region_id != policy.region_id
        ):
            raise BusinessRuleError("Assigned adjuster must be active and belong to the policy region")
    if payload.claim_number and db.scalar(
        select(Claim).where(Claim.claim_number == payload.claim_number)
    ):
        raise BusinessRuleError("A claim with this claim number already exists")

    claim = Claim(
        claim_number=payload.claim_number or f"CLM-{uuid.uuid4().hex[:12].upper()}",
        policy_id=policy.id,
        region_id=policy.region_id,
        claim_type=payload.claim_type,
        claimant_name=payload.claimant_name,
        claimant_email=payload.claimant_email,
        claimant_phone=payload.claimant_phone,
        # National identifiers are not returned or written to audit records.
        claimant_national_id_enc=(
            encrypt_sensitive_value(payload.claimant_national_id)
            if payload.claimant_national_id
            else None
        ),
        incident_date=payload.incident_date,
        description=payload.description,
        claimed_amount=payload.claimed_amount,
        is_high_value=payload.claimed_amount >= Decimal(str(settings.HIGH_VALUE_THRESHOLD)),
        assigned_adjuster_id=payload.assigned_adjuster_id,
        created_by=actor.id,
        sla_due_at=datetime.now(UTC) + timedelta(days=settings.SLA_DEFAULT_DAYS),
    )
    db.add(claim)
    db.flush()
    db.add(
        ClaimStatusHistory(
            claim_id=claim.id,
            from_status=None,
            to_status=ClaimStatus.SUBMITTED,
            changed_by=actor.id,
            changed_at=datetime.now(UTC),
        )
    )
    log_action(
        db,
        action="CLAIM_CREATED",
        entity_type="claim",
        entity_id=str(claim.id),
        actor=actor,
        new={"claim_number": claim.claim_number, "status": ClaimStatus.SUBMITTED.value},
        request=request,
    )
    db.commit()
    db.refresh(claim)
    return claim


_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
    ClaimStatus.SUBMITTED: {ClaimStatus.UNDER_REVIEW},
    ClaimStatus.UNDER_REVIEW: {ClaimStatus.APPROVED, ClaimStatus.REJECTED},
    ClaimStatus.APPROVED: {ClaimStatus.CLOSED},
    ClaimStatus.REJECTED: {ClaimStatus.CLOSED},
    ClaimStatus.CLOSED: set(),
}


def change_status(
    db: Session,
    claim: Claim,
    payload: ClaimStatusUpdate,
    *,
    actor: User,
    request: Request | None = None,
) -> Claim:
    old_status = (
        claim.status
        if isinstance(claim.status, ClaimStatus)
        else ClaimStatus(claim.status)
    )
    new_status = (
        payload.status
        if isinstance(payload.status, ClaimStatus)
        else ClaimStatus(payload.status)
    )
    is_manager = actor.role in (UserRole.ADMIN, UserRole.CLAIMS_MANAGER)
    normal_transition = new_status in _TRANSITIONS[old_status]
    is_override = not normal_transition

    if is_override:
        if not is_manager:
            raise BusinessRuleError("This status transition is not permitted")
        if not payload.justification:
            raise BusinessRuleError("A justification is required for a status override")
        forward_transitions = {
            ClaimStatus.SUBMITTED: {
                ClaimStatus.UNDER_REVIEW,
                ClaimStatus.APPROVED,
                ClaimStatus.REJECTED,
                ClaimStatus.CLOSED,
            },
            ClaimStatus.UNDER_REVIEW: {
                ClaimStatus.APPROVED,
                ClaimStatus.REJECTED,
                ClaimStatus.CLOSED,
            },
            ClaimStatus.APPROVED: {ClaimStatus.CLOSED},
            ClaimStatus.REJECTED: {ClaimStatus.CLOSED},
            ClaimStatus.CLOSED: set(),
        }
        if new_status not in forward_transitions[old_status]:
            raise BusinessRuleError("Status transitions must move forward")
    elif new_status == ClaimStatus.APPROVED and claim.is_high_value and not is_manager:
        raise BusinessRuleError("High-value claims require manager approval")

    if payload.approved_amount is not None and new_status != ClaimStatus.APPROVED:
        raise BusinessRuleError("approved_amount is only valid when approving a claim")
    if (
        payload.approved_amount is not None
        and payload.approved_amount > claim.claimed_amount
    ):
        raise BusinessRuleError("approved_amount cannot exceed claimed_amount")
    if new_status == ClaimStatus.APPROVED and payload.approved_amount is not None:
        claim.approved_amount = payload.approved_amount
    if new_status in (ClaimStatus.APPROVED, ClaimStatus.REJECTED):
        claim.decided_at = datetime.now(UTC)
    if new_status == ClaimStatus.CLOSED:
        claim.closed_at = datetime.now(UTC)
    claim.status = new_status

    db.add(
        ClaimStatusHistory(
            claim_id=claim.id,
            from_status=old_status,
            to_status=new_status,
            changed_by=actor.id,
            is_override=is_override,
            justification=payload.justification,
            changed_at=datetime.now(UTC),
        )
    )
    if payload.note:
        db.add(
            ClaimNote(
                claim_id=claim.id,
                author_id=actor.id,
                note_type=(
                    NoteType.MANAGER_NOTE if is_manager else NoteType.ADJUSTER_NOTE
                ),
                content=payload.note,
            )
        )
    log_action(
        db,
        action="CLAIM_STATUS_CHANGED",
        entity_type="claim",
        entity_id=str(claim.id),
        actor=actor,
        old={"status": _enum_value(old_status)},
        new={"status": _enum_value(new_status), "override": is_override},
        request=request,
    )
    db.commit()
    db.refresh(claim)
    return claim
