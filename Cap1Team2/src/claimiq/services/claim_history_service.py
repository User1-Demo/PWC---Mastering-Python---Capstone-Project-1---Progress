from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.claim import Claim
from claimiq.models.claim_status_history import ClaimStatusHistory


def get_claim_status_history(
    db: Session,
    claim_id: int,
) -> list[ClaimStatusHistory]:
    """Return the status history for an existing claim."""

    claim = db.get(Claim, claim_id)

    if claim is None:
        raise ValueError("Claim not found")

    statement = (
        select(ClaimStatusHistory)
        .where(
            ClaimStatusHistory.claim_id == claim_id,
        )
        .order_by(
            ClaimStatusHistory.created_at,
            ClaimStatusHistory.id,
        )
    )

    return list(db.scalars(statement).all())