"""
workflow.py (claims module)

Purpose: Defines the claim status state machine. This is the ONLY
place that knows which status transitions are legal - the service
layer calls validate_transition() rather than hardcoding rules
inline, so the rules stay in one testable location.

Reference: SRS BR-003 - "Claim status can only move forward through
defined states unless a Manager override with justification is
recorded."
"""

from src.common.enums import ClaimStatus

# Maps: current status -> list of statuses it's allowed to move to NEXT
ALLOWED_TRANSITIONS: dict[str, list[str]] = {
    ClaimStatus.SUBMITTED.value: [ClaimStatus.VALIDATION.value],
    ClaimStatus.VALIDATION.value: [ClaimStatus.ASSIGNED.value, ClaimStatus.REJECTED.value],
    ClaimStatus.ASSIGNED.value: [ClaimStatus.UNDER_REVIEW.value],
    ClaimStatus.UNDER_REVIEW.value: [ClaimStatus.AI_MANAGER_REVIEW.value],
    ClaimStatus.AI_MANAGER_REVIEW.value: [ClaimStatus.APPROVED.value, ClaimStatus.REJECTED.value],
    ClaimStatus.APPROVED.value: [ClaimStatus.CLOSED.value],
    ClaimStatus.REJECTED.value: [ClaimStatus.CLOSED.value],
}


class InvalidTransitionError(Exception):
    """Raised when a status change doesn't follow the allowed workflow."""
    pass


class OverrideJustificationRequiredError(Exception):
    """Raised when override_flag=True but no justification was given."""
    pass


def validate_transition(
    from_status: str,
    to_status: str,
    override_flag: bool,
    override_justification: str | None,
) -> None:
    """
    Raises an exception if the transition is invalid.
    Returns silently (None) if the transition is allowed.
    """
    if override_flag:
        if not override_justification or not override_justification.strip():
            raise OverrideJustificationRequiredError(
                "override_justification is required when override_flag is True"
            )
        # BR-003: a valid override bypasses the normal transition table entirely
        return

    allowed_next_states = ALLOWED_TRANSITIONS.get(from_status, [])
    if to_status not in allowed_next_states:
        raise InvalidTransitionError(
            f"Cannot transition from '{from_status}' to '{to_status}' "
            f"without a Manager override. Allowed next states from "
            f"'{from_status}': {allowed_next_states}"
        )