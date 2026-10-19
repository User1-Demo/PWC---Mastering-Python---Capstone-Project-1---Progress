from datetime import UTC

from sqlalchemy.orm import Session

from claimiq.models.claim import Claim, ClaimStatus
from claimiq.models.claim_status_history import (
    ClaimStatusHistory,
    ClaimStatusHistoryStatus,
)
from claimiq.schemas.claim import ClaimStatusUpdate
from claimiq.services.audit_service import create_audit_log
from claimiq.services.claim_service import get_claim_by_id
from claimiq.services.claim_workflow import validate_status_transition


def update_claim_status(
    db: Session,
    claim_id: int,
    status_data: ClaimStatusUpdate,
    actor_user_id: int,
) -> Claim:
    """Validate and update a claim status."""

    claim = get_claim_by_id(
        db=db,
        claim_id=claim_id,
    )

    if claim is None:
        raise ValueError("Claim not found")

    current_status = claim.status
    new_status = status_data.status

    validate_status_transition(
        current_status=current_status,
        new_status=new_status,
    )

    if (
        new_status == ClaimStatus.REJECTED
        and not status_data.reason
    ):
        raise ValueError(
            "A rejection reason is required",
        )

    if (
        new_status == ClaimStatus.APPROVED
        and status_data.approved_amount is None
    ):
        raise ValueError(
            "Approved amount is required",
        )

    previous_status = ClaimStatusHistoryStatus(
        current_status.value,
    )

    history_status = ClaimStatusHistoryStatus(
        new_status.value,
    )

    claim.status = new_status

    if status_data.approved_amount is not None:
        claim.approved_amount = status_data.approved_amount

    if status_data.reason is not None:
        claim.decision_reason = status_data.reason

    if new_status in {
        ClaimStatus.APPROVED,
        ClaimStatus.REJECTED,
    }:
        from datetime import datetime

        claim.decision_date = datetime.now(UTC)

    if new_status == ClaimStatus.CLOSED:
        from datetime import datetime

        claim.closed_at = datetime.now(UTC)

    db.commit()
    db.refresh(claim)

    history = ClaimStatusHistory(
        claim_id=claim.id,
        previous_status=previous_status,
        new_status=history_status,
        changed_by=actor_user_id,
        reason=status_data.reason,
    )

    db.add(history)
    db.commit()
    db.refresh(history)

    create_audit_log(
        db=db,
        action="CLAIM_STATUS_CHANGED",
        user_id=actor_user_id,
        entity_type="Claim",
        entity_id=claim.id,
        metadata={
            "previous_status": current_status.value,
            "new_status": new_status.value,
            "reason_provided": status_data.reason is not None,
        },
    )

    return claim