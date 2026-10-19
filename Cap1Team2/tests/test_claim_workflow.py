import pytest

from claimiq.models.claim import ClaimStatus
from claimiq.services.claim_workflow import (
    validate_status_transition,
)


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            ClaimStatus.SUBMITTED,
            ClaimStatus.VALIDATION,
        ),
        (
            ClaimStatus.VALIDATION,
            ClaimStatus.ASSIGNED,
        ),
        (
            ClaimStatus.ASSIGNED,
            ClaimStatus.UNDER_REVIEW,
        ),
        (
            ClaimStatus.UNDER_REVIEW,
            ClaimStatus.AI_MANAGER_REVIEW,
        ),
        (
            ClaimStatus.UNDER_REVIEW,
            ClaimStatus.APPROVED,
        ),
        (
            ClaimStatus.UNDER_REVIEW,
            ClaimStatus.REJECTED,
        ),
        (
            ClaimStatus.AI_MANAGER_REVIEW,
            ClaimStatus.APPROVED,
        ),
        (
            ClaimStatus.AI_MANAGER_REVIEW,
            ClaimStatus.REJECTED,
        ),
        (
            ClaimStatus.APPROVED,
            ClaimStatus.CLOSED,
        ),
        (
            ClaimStatus.REJECTED,
            ClaimStatus.CLOSED,
        ),
    ],
)
def test_valid_status_transition(
    current_status: ClaimStatus,
    new_status: ClaimStatus,
) -> None:
    validate_status_transition(
        current_status=current_status,
        new_status=new_status,
    )


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (
            ClaimStatus.CLOSED,
            ClaimStatus.UNDER_REVIEW,
        ),
        (
            ClaimStatus.APPROVED,
            ClaimStatus.SUBMITTED,
        ),
        (
            ClaimStatus.REJECTED,
            ClaimStatus.APPROVED,
        ),
        (
            ClaimStatus.SUBMITTED,
            ClaimStatus.CLOSED,
        ),
    ],
)
def test_invalid_status_transition(
    current_status: ClaimStatus,
    new_status: ClaimStatus,
) -> None:
    with pytest.raises(
        ValueError,
        match="Invalid claim status transition",
    ):
        validate_status_transition(
            current_status=current_status,
            new_status=new_status,
        )


def test_same_status_transition_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="already in the requested status",
    ):
        validate_status_transition(
            current_status=ClaimStatus.SUBMITTED,
            new_status=ClaimStatus.SUBMITTED,
        )