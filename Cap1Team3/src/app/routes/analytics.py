from typing import Annotated

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.app.core.security import get_current_user
from src.app.db.models import Claim, ClaimStatus, ClaimType, User, UserRole
from src.app.db.session import get_db
from src.app.schemas.analytics import ClaimsAnalyticsResponse

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]

DEFAULT_SLA_DAYS = 7


def require_manager_or_admin(current_user: User) -> None:
    if current_user.role not in [UserRole.ADMIN, UserRole.CLAIMS_MANAGER]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only claims managers or admins can access analytics",
        )


@router.get(
    "/claims",
    response_model=ClaimsAnalyticsResponse,
)
def get_claims_analytics(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
    region: str | None = Query(default=None),
    claim_type: ClaimType | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    sla_days: int = Query(default=DEFAULT_SLA_DAYS, ge=1, le=365),
):
    require_manager_or_admin(current_user)

    query = (
        select(
            Claim.id,
            Claim.claim_number,
            Claim.claim_type,
            Claim.region,
            Claim.status,
            Claim.assigned_adjuster_id,
            Claim.submitted_at,
            Claim.closed_at,
            Claim.created_at,
            Claim.updated_at,
            User.full_name.label("adjuster_name"),
        )
        .select_from(Claim)
        .outerjoin(User, Claim.assigned_adjuster_id == User.id)
    )

    results = db.execute(query).all()

    if not results:
        return ClaimsAnalyticsResponse(
            total_claims=0,
            approved_claims=0,
            rejected_claims=0,
            closed_claims=0,
            approval_rate=0.0,
            rejection_rate=0.0,
            average_turnaround_days=0.0,
            sla_breached_claims=0,
            claims_by_status={},
            claims_by_region={},
            claims_by_type={},
            monthly_claim_volume={},
            adjuster_workload={},
        )

    rows = []
    for row in results:
        rows.append(
            {
                "id": row.id,
                "claim_number": row.claim_number,
                "claim_type": row.claim_type.value if row.claim_type else None,
                "region": row.region,
                "status": row.status.value if row.status else None,
                "assigned_adjuster_id": row.assigned_adjuster_id,
                "adjuster_name": row.adjuster_name,
                "submitted_at": row.submitted_at,
                "closed_at": row.closed_at,
                "created_at": row.created_at,
                "updated_at": row.updated_at,
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        return ClaimsAnalyticsResponse(
            total_claims=0,
            approved_claims=0,
            rejected_claims=0,
            closed_claims=0,
            approval_rate=0.0,
            rejection_rate=0.0,
            average_turnaround_days=0.0,
            sla_breached_claims=0,
            claims_by_status={},
            claims_by_region={},
            claims_by_type={},
            monthly_claim_volume={},
            adjuster_workload={},
        )

    df["submitted_at"] = pd.to_datetime(df["submitted_at"], errors="coerce")
    df["closed_at"] = pd.to_datetime(df["closed_at"], errors="coerce")
    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
    df["updated_at"] = pd.to_datetime(df["updated_at"], errors="coerce")

    if region:
        df = df[df["region"] == region]

    if claim_type:
        df = df[df["claim_type"] == claim_type.value]

    if start_date:
        start_ts = pd.to_datetime(start_date, errors="coerce")
        if pd.isna(start_ts):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid start_date format. Use YYYY-MM-DD",
            )
        df = df[df["submitted_at"] >= start_ts]

    if end_date:
        end_ts = pd.to_datetime(end_date, errors="coerce")
        if pd.isna(end_ts):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid end_date format. Use YYYY-MM-DD",
            )
        df = df[df["submitted_at"] <= end_ts]

    if df.empty:
        return ClaimsAnalyticsResponse(
            total_claims=0,
            approved_claims=0,
            rejected_claims=0,
            closed_claims=0,
            approval_rate=0.0,
            rejection_rate=0.0,
            average_turnaround_days=0.0,
            sla_breached_claims=0,
            claims_by_status={},
            claims_by_region={},
            claims_by_type={},
            monthly_claim_volume={},
            adjuster_workload={},
        )

    total_claims = len(df)
    approved_claims = int((df["status"] == ClaimStatus.APPROVED.value).sum())
    rejected_claims = int((df["status"] == ClaimStatus.REJECTED.value).sum())
    closed_claims = int((df["status"] == ClaimStatus.CLOSED.value).sum())

    approval_rate = round((approved_claims / total_claims) * 100, 2) if total_claims else 0.0
    rejection_rate = round((rejected_claims / total_claims) * 100, 2) if total_claims else 0.0

    closed_df = df[df["closed_at"].notna()].copy()
    if not closed_df.empty:
        closed_df["turnaround_days"] = (
            closed_df["closed_at"] - closed_df["submitted_at"]
        ).dt.days
        average_turnaround_days = round(
            float(closed_df["turnaround_days"].mean()),
            2,
        )
    else:
        average_turnaround_days = 0.0

    now_ts = pd.Timestamp.now()
    open_df = df[df["closed_at"].isna()].copy()
    if not open_df.empty:
        open_df["open_days"] = (now_ts - open_df["submitted_at"]).dt.days
        sla_breached_claims = int((open_df["open_days"] > sla_days).sum())
    else:
        sla_breached_claims = 0

    claims_by_status = {
        str(k): int(v)
        for k, v in df["status"].value_counts(dropna=False).to_dict().items()
    }

    claims_by_region = {
        str(k): int(v)
        for k, v in df["region"].value_counts(dropna=False).to_dict().items()
    }

    claims_by_type = {
        str(k): int(v)
        for k, v in df["claim_type"].value_counts(dropna=False).to_dict().items()
    }

    monthly_series = (
        df.assign(month=df["submitted_at"].dt.to_period("M").astype(str))
        .groupby("month")
        .size()
        .sort_index()
    )
    monthly_claim_volume = {
        str(k): int(v)
        for k, v in monthly_series.to_dict().items()
    }

    df["adjuster_label"] = df["adjuster_name"].fillna("Unassigned")

    workload_series = (
        df["adjuster_label"]
        .value_counts(dropna=False)
    )
    adjuster_workload = {
        str(k): int(v)
        for k, v in workload_series.to_dict().items()
    }

    return ClaimsAnalyticsResponse(
        total_claims=total_claims,
        approved_claims=approved_claims,
        rejected_claims=rejected_claims,
        closed_claims=closed_claims,
        approval_rate=approval_rate,
        rejection_rate=rejection_rate,
        average_turnaround_days=average_turnaround_days,
        sla_breached_claims=sla_breached_claims,
        claims_by_status=claims_by_status,
        claims_by_region=claims_by_region,
        claims_by_type=claims_by_type,
        monthly_claim_volume=monthly_claim_volume,
        adjuster_workload=adjuster_workload,
    )