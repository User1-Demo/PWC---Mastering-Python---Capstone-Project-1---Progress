from unittest.mock import Mock

import pytest

from claimiq.models.claim import Claim
from claimiq.models.claim_status_history import (
    ClaimStatusHistory,
    ClaimStatusHistoryStatus,
)
from claimiq.services.claim_history_service import (
    get_claim_status_history,
)


def test_get_claim_status_history_successfully() -> None:
    db = Mock()

    claim = Claim(id=1)
    history = [
        ClaimStatusHistory(
            id=1,
            claim_id=1,
            previous_status=None,
            new_status=ClaimStatusHistoryStatus.SUBMITTED,
            changed_by=1,
            reason=None,
        ),
        ClaimStatusHistory(
            id=2,
            claim_id=1,
            previous_status=ClaimStatusHistoryStatus.SUBMITTED,
            new_status=ClaimStatusHistoryStatus.VALIDATION,
            changed_by=1,
            reason="Initial validation started",
        ),
    ]

    db.get.return_value = claim
    db.scalars.return_value.all.return_value = history

    result = get_claim_status_history(
        db=db,
        claim_id=1,
    )

    assert result == history
    db.get.assert_called_once_with(Claim, 1)


def test_get_claim_status_history_rejects_missing_claim() -> None:
    db = Mock()
    db.get.return_value = None

    with pytest.raises(
        ValueError,
        match="Claim not found",
    ):
        get_claim_status_history(
            db=db,
            claim_id=999,
        )

    db.scalars.assert_not_called()