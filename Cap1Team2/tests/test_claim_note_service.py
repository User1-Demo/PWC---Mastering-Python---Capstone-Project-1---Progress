from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from claimiq.models.claim import Claim, ClaimStatus
from claimiq.schemas.claim_note import ClaimNoteCreate
from claimiq.services.claim_note_service import create_claim_note


def existing_claim() -> Claim:
    return Claim(
        id=1,
        claim_number="CLM-10001",
        policy_id=1,
        assigned_adjuster_id=None,
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


def test_create_claim_note_successfully() -> None:
    db = Mock()
    db.get.return_value = existing_claim()

    note_data = ClaimNoteCreate(
        note_text="Claim documents reviewed successfully.",
    )

    note = create_claim_note(
        db=db,
        claim_id=1,
        author_id=2,
        note_data=note_data,
    )

    assert note.claim_id == 1
    assert note.author_id == 2
    assert note.note_text == (
        "Claim documents reviewed successfully."
    )

    # First add: ClaimNote
    # Second add: AuditLog
    assert db.add.call_count == 2

    # First commit: ClaimNote
    # Second commit: AuditLog
    assert db.commit.call_count == 2

    audit_log = db.add.call_args_list[-1].args[0]

    assert audit_log.action == "CLAIM_NOTE_CREATED"
    assert audit_log.user_id == 2
    assert audit_log.entity_type == "ClaimNote"
    assert audit_log.entity_id == note.id
    assert audit_log.metadata_json == {
        "claim_id": 1,
    }


def test_create_claim_note_rejects_missing_claim() -> None:
    db = Mock()
    db.get.return_value = None

    note_data = ClaimNoteCreate(
        note_text="This claim does not exist.",
    )

    with pytest.raises(
        ValueError,
        match="Claim not found",
    ):
        create_claim_note(
            db=db,
            claim_id=999,
            author_id=2,
            note_data=note_data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()