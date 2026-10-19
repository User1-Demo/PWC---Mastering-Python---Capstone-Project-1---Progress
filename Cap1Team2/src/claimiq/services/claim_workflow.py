from claimiq.models.claim import ClaimStatus

VALID_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
    ClaimStatus.SUBMITTED: {
        ClaimStatus.VALIDATION,
    },
    ClaimStatus.VALIDATION: {
        ClaimStatus.ASSIGNED,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.ASSIGNED: {
        ClaimStatus.UNDER_REVIEW,
    },
    ClaimStatus.UNDER_REVIEW: {
        ClaimStatus.AI_MANAGER_REVIEW,
        ClaimStatus.APPROVED,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.AI_MANAGER_REVIEW: {
        ClaimStatus.APPROVED,
        ClaimStatus.REJECTED,
    },
    ClaimStatus.APPROVED: {
        ClaimStatus.CLOSED,
    },
    ClaimStatus.REJECTED: {
        ClaimStatus.CLOSED,
    },
    ClaimStatus.CLOSED: set(),
}


def validate_status_transition(
    current_status: ClaimStatus,
    new_status: ClaimStatus,
) -> None:
    """Validate whether a claim status transition is allowed."""

    if current_status == new_status:
        raise ValueError(
            "Claim is already in the requested status",
        )

    allowed_statuses = VALID_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            f"Invalid claim status transition: "
            f"{current_status.value} to {new_status.value}",
        )