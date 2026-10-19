from datetime import date, datetime, time, timedelta, timezone
import uuid

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.db.session import get_db
from app.models.claim import Claim
from app.models.audit import ChatQueryLog
from app.models.enums import ClaimStatus, PolicyType, UserRole
from app.models.policy import Policy
from app.models.user import Region, User
from app.schemas.analytics import AIAnalytics, AnalyticsPoint, ClaimsAnalytics

router = APIRouter(prefix="/analytics", tags=["analytics"])
manager_only = require_roles(UserRole.ADMIN, UserRole.CLAIMS_MANAGER)


def _points(series: pd.Series) -> list[AnalyticsPoint]:
    counts = series.value_counts().sort_index()
    return [
        AnalyticsPoint(label=str(label), count=int(count))
        for label, count in counts.items()
    ]


def _top_points(series: pd.Series, limit: int = 10) -> list[AnalyticsPoint]:
    return [
        AnalyticsPoint(label=str(label), count=int(count))
        for label, count in series.value_counts().head(limit).items()
    ]


def _validate_date_range(date_from: date | None, date_to: date | None) -> None:
    if date_from is not None and date_to is not None and date_from > date_to:
        raise HTTPException(
            status_code=422,
            detail="date_from must be earlier than or equal to date_to",
        )


@router.get("/claims", response_model=ClaimsAnalytics)
def claims_analytics(
    date_from: date | None = None,
    date_to: date | None = None,
    region_id: uuid.UUID | None = None,
    claim_type: PolicyType | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(manager_only),
) -> ClaimsAnalytics:
    _validate_date_range(date_from, date_to)
    query = select(Claim).join(Policy)
    if region_id is not None:
        query = query.where(Claim.region_id == region_id)
    if claim_type is not None:
        query = query.where(Claim.claim_type == claim_type)
    if date_from is not None:
        query = query.where(
            Claim.submitted_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        query = query.where(
            Claim.submitted_at
            < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        )

    claims = list(db.scalars(query))
    rows = [
        {
            "id": str(claim.id),
            "status": claim.status.value,
            "claim_type": claim.claim_type.value,
            "region_id": str(claim.region_id),
            "adjuster_id": str(claim.assigned_adjuster_id) if claim.assigned_adjuster_id else None,
            "submitted_at": claim.submitted_at,
            "decided_at": claim.decided_at,
            "sla_due_at": claim.sla_due_at,
        }
        for claim in claims
    ]
    frame = pd.DataFrame(
        rows,
        columns=[
            "id", "status", "claim_type", "region_id", "adjuster_id",
            "submitted_at", "decided_at", "sla_due_at",
        ],
    )
    if frame.empty:
        return ClaimsAnalytics(
            total_claims=0,
            approved_claims=0,
            rejected_claims=0,
            approval_rate=0.0,
            average_turnaround_hours=None,
            sla_compliance_rate=None,
            open_claims=0,
        )

    frame = frame.drop_duplicates(subset=["id"]).dropna(
        subset=["id", "status", "submitted_at"]
    )
    frame["submitted_at"] = pd.to_datetime(frame["submitted_at"], utc=True)
    frame["decided_at"] = pd.to_datetime(frame["decided_at"], utc=True)
    frame["sla_due_at"] = pd.to_datetime(frame["sla_due_at"], utc=True)
    frame["turnaround_hours"] = (
        frame["decided_at"] - frame["submitted_at"]
    ).dt.total_seconds() / 3600

    total = len(frame)
    approved = int((frame["status"] == ClaimStatus.APPROVED.value).sum())
    rejected = int((frame["status"] == ClaimStatus.REJECTED.value).sum())
    decided = frame[frame["decided_at"].notna()]
    open_statuses = {
        ClaimStatus.SUBMITTED.value,
        ClaimStatus.UNDER_REVIEW.value,
    }
    open_claims = frame["status"].isin(open_statuses)
    breached = open_claims & frame["sla_due_at"].lt(pd.Timestamp.now(tz="UTC"))
    sla_decided = decided[decided["sla_due_at"].notna()]
    sla_met_count = int(
        (sla_decided["decided_at"] <= sla_decided["sla_due_at"]).sum()
    )

    region_ids = [
        uuid.UUID(region) for region in frame["region_id"].dropna().unique()
    ]
    region_names = dict(
        db.execute(
            select(Region.id, Region.name).where(Region.id.in_(region_ids))
        ).all()
    )
    adjuster_ids = [
        uuid.UUID(adjuster) for adjuster in frame["adjuster_id"].dropna().unique()
    ]
    adjuster_names = dict(
        db.execute(
            select(User.id, User.full_name).where(User.id.in_(adjuster_ids))
        ).all()
    )
    submitted_month = frame["submitted_at"].dt.strftime("%Y-%m")
    regions = frame["region_id"].map(
        lambda region: region_names.get(uuid.UUID(region), "Unknown region")
    )
    adjusters = frame["adjuster_id"].map(
        lambda adjuster: (
            adjuster_names.get(uuid.UUID(adjuster), "Unknown adjuster")
            if adjuster
            else "Unassigned"
        )
    )

    return ClaimsAnalytics(
        total_claims=total,
        approved_claims=approved,
        rejected_claims=rejected,
        approval_rate=round(approved / (approved + rejected) * 100, 2)
        if approved + rejected
        else 0.0,
        average_turnaround_hours=round(float(decided["turnaround_hours"].mean()), 2)
        if not decided.empty
        else None,
        sla_compliance_rate=round(sla_met_count / len(sla_decided) * 100, 2)
        if len(sla_decided)
        else None,
        open_claims=int(open_claims.sum()),
        sla_breached_claims=int(breached.sum()),
        by_month=_points(submitted_month),
        by_region=_points(regions),
        by_claim_type=_points(frame["claim_type"]),
        adjuster_workload=_points(adjusters),
    )


@router.get("/ai", response_model=AIAnalytics)
def ai_analytics(
    date_from: date | None = None,
    date_to: date | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(manager_only),
) -> AIAnalytics:
    _validate_date_range(date_from, date_to)
    query = select(ChatQueryLog)
    if date_from is not None:
        query = query.where(
            ChatQueryLog.created_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to is not None:
        query = query.where(
            ChatQueryLog.created_at
            < datetime.combine(date_to + timedelta(days=1), time.min, tzinfo=timezone.utc)
        )
    logs = list(db.scalars(query))
    if not logs:
        return AIAnalytics(total_queries=0, no_match_queries=0, flagged_queries=0)

    frame = pd.DataFrame(
        [
            {
                "id": str(log.id),
                "question": log.question,
                "created_at": log.created_at,
                "is_no_match": log.is_no_match,
                "flagged_for_review": log.flagged_for_review,
            }
            for log in logs
        ]
    ).drop_duplicates(subset=["id"])
    frame["created_at"] = pd.to_datetime(frame["created_at"], utc=True)
    words = (
        frame["question"]
        .str.lower()
        .str.findall(r"[a-z0-9]{3,}")
        .explode()
        .dropna()
    )
    excluded = {
        "about", "after", "also", "and", "are", "can", "does", "for",
        "from", "how", "into", "its", "what", "when", "where", "which",
        "with", "would", "your", "the", "this", "that", "was", "were",
    }
    words = words[~words.isin(excluded)]
    return AIAnalytics(
        total_queries=len(frame),
        no_match_queries=int(frame["is_no_match"].sum()),
        flagged_queries=int(frame["flagged_for_review"].sum()),
        by_month=_points(frame["created_at"].dt.strftime("%Y-%m")),
        top_terms=_top_points(words),
    )
