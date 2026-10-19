
import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.claim import Claim

DEFAULT_SLA_DAYS = 5


def get_claim_analytics(
    db: Session,
    *,
    sla_days: int = DEFAULT_SLA_DAYS,
) -> dict:
    """Calculate claim analytics using Pandas."""

    statement = select(Claim).order_by(Claim.id)
    claims = list(db.scalars(statement).all())

    if not claims:
        return {
            "total_claims": 0,
            "claims_by_status": {},
            "total_claimed_amount": 0.0,
            "total_approved_amount": 0.0,
            "approval_rate": 0.0,
            "rejection_rate": 0.0,
            "average_turnaround_days": 0.0,
            "sla_breaches": 0,
        }

    records = [
        {
            "status": claim.status.value,
            "claimed_amount": float(
                claim.claimed_amount or 0,
            ),
            "approved_amount": float(
                claim.approved_amount or 0,
            ),
            "submitted_at": claim.submitted_at,
            "decision_date": claim.decision_date,
        }
        for claim in claims
    ]

    dataframe = pd.DataFrame(records)

    dataframe["submitted_at"] = pd.to_datetime(
        dataframe["submitted_at"],
        utc=True,
        errors="coerce",
    )

    dataframe["decision_date"] = pd.to_datetime(
        dataframe["decision_date"],
        utc=True,
        errors="coerce",
    )

    dataframe["turnaround_days"] = (
        dataframe["decision_date"]
        - dataframe["submitted_at"]
    ).dt.total_seconds() / 86400

    completed_claims = dataframe[
        dataframe["status"].isin(["APPROVED", "REJECTED"])
    ]

    approval_count = int(
        (dataframe["status"] == "APPROVED").sum(),
    )

    rejection_count = int(
        (dataframe["status"] == "REJECTED").sum(),
    )

    completed_count = len(completed_claims)

    approval_rate = (
        approval_count / completed_count * 100
        if completed_count
        else 0.0
    )

    rejection_rate = (
        rejection_count / completed_count * 100
        if completed_count
        else 0.0
    )

    valid_turnaround = dataframe[
        dataframe["turnaround_days"].notna()
    ]

    average_turnaround_days = (
        float(valid_turnaround["turnaround_days"].mean())
        if not valid_turnaround.empty
        else 0.0
    )

    sla_breaches = int(
        (
            valid_turnaround["turnaround_days"]
            > sla_days
        ).sum(),
    )

    claims_by_status = {
        str(status): int(count)
        for status, count in (
            dataframe["status"].value_counts().items()
        )
    }

    return {
        "total_claims": len(dataframe),
        "claims_by_status": claims_by_status,
        "total_claimed_amount": float(
            dataframe["claimed_amount"].sum(),
        ),
        "total_approved_amount": float(
            dataframe["approved_amount"].sum(),
        ),
        "approval_rate": round(approval_rate, 2),
        "rejection_rate": round(rejection_rate, 2),
        "average_turnaround_days": round(
            average_turnaround_days,
            2,
        ),
        "sla_breaches": sla_breaches,
    }