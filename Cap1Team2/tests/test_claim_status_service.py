from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from claimiq.models.claim import Claim, ClaimStatus
from claimiq.models.claim_status_history import (
    ClaimStatusHistory,
    ClaimStatusHistoryStatus,
)
from claimiq.schemas.claim import ClaimStatusUpdate
from claimiq.services.claim_status_service import update_claim_status


def existing_claim() -> Claim:
    return Claim(
        id=1,
        claim_number="CLM-10001",
        policy_id=1,
        assigned_adjuster_id=2,
        claim_type="Vehicle Damage",
        incident_date=date(2025, 3, 10),
        claimed_amount=Decimal("8500.00"),
        approved_amount=None,
        status=ClaimStatus.SUBMITTED,
        description="Vehicle damage caused by an accident",
        decision_reason=None,
        decision_date=None,
        closed_at=None,
    )


def test_submitted_claim_can_move_to_validation() -> None:
    db = Mock()
    claim = existing_claim()
    db.get.return_value = claim

    result = update_claim_status(
        db=db,
        claim_id=1,
        status_data=ClaimStatusUpdate(
            status=ClaimStatus.VALIDATION,
        ),
        actor_user_id=2,
    )

    assert result is claim
    assert claim.status == ClaimStatus.VALIDATION

    # The service adds:
    # 1. ClaimStatusHistory
    # 2. AuditLog
    assert db.add.call_count == 2

    # Claim update, history insert, and audit-log insert.
    assert db.commit.call_count == 3

    history = next(
        item.args[0]
        for item in db.add.call_args_list
        if isinstance(item.args[0], ClaimStatusHistory)
    )

    assert history.claim_id == 1
    assert history.previous_status == (
        ClaimStatusHistoryStatus.SUBMITTED
    )
    assert history.new_status == (
        ClaimStatusHistoryStatus.VALIDATION
    )
    assert history.changed_by == 2


def test_rejection_requires_reason() -> None:
    db = Mock()
    claim = existing_claim()
    claim.status = ClaimStatus.UNDER_REVIEW
    db.get.return_value = claim

    with pytest.raises(
        ValueError,
        match="rejection reason is required",
    ):
        update_claim_status(
            db=db,
            claim_id=1,
            status_data=ClaimStatusUpdate(
                status=ClaimStatus.REJECTED,
            ),
            actor_user_id=2,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_approval_requires_approved_amount() -> None:
    db = Mock()
    claim = existing_claim()
    claim.status = ClaimStatus.UNDER_REVIEW
    db.get.return_value = claim

    with pytest.raises(
        ValueError,
        match="Approved amount is required",
    ):
        update_claim_status(
            db=db,
            claim_id=1,
            status_data=ClaimStatusUpdate(
                status=ClaimStatus.APPROVED,
                reason="Coverage verified.",
            ),
            actor_user_id=2,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_claim_can_be_approved_with_amount() -> None:
    db = Mock()
    claim = existing_claim()
    claim.status = ClaimStatus.UNDER_REVIEW
    db.get.return_value = claim

    result = update_claim_status(
        db=db,
        claim_id=1,
        status_data=ClaimStatusUpdate(
            status=ClaimStatus.APPROVED,
            approved_amount=Decimal("8000.00"),
            reason="Coverage verified and claim approved.",
        ),
        actor_user_id=2,
    )

    assert result.status == ClaimStatus.APPROVED
    assert result.approved_amount == Decimal("8000.00")
    assert result.decision_reason == (
        "Coverage verified and claim approved."
    )

    audit_log = next(
        item.args[0]
        for item in db.add.call_args_list
        if item.args[0].__class__.__name__ == "AuditLog"
    )

    assert audit_log.action == "CLAIM_STATUS_CHANGED"
    assert audit_log.user_id == 2
    assert audit_log.entity_type == "Claim"
    assert audit_log.entity_id == 1
    assert audit_log.metadata_json == {
        "previous_status": "UNDER_REVIEW",
        "new_status": "APPROVED",
        "reason_provided": True,
    }


def test_invalid_status_transition_is_rejected() -> None:
    db = Mock()
    claim = existing_claim()
    claim.status = ClaimStatus.CLOSED
    db.get.return_value = claim

    with pytest.raises(
        ValueError,
        match="Invalid claim status transition",
    ):
        update_claim_status(
            db=db,
            claim_id=1,
            status_data=ClaimStatusUpdate(
                status=ClaimStatus.UNDER_REVIEW,
            ),
            actor_user_id=2,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_missing_claim_is_rejected() -> None:
    db = Mock()
    db.get.return_value = None

    with pytest.raises(
        ValueError,
        match="Claim not found",
    ):
        update_claim_status(
            db=db,
            claim_id=999,
            status_data=ClaimStatusUpdate(
                status=ClaimStatus.VALIDATION,
            ),
            actor_user_id=2,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()