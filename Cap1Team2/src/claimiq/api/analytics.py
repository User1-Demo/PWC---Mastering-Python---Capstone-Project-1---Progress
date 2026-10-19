from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from claimiq.core.permissions import require_manager_or_admin
from claimiq.db.database import get_db
from claimiq.models.user import User
from claimiq.schemas.analytics import ClaimAnalyticsResponse
from claimiq.services.analytics_service import get_claim_analytics

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"],
)


ManagerOrAdminUser = Annotated[
    User,
    Depends(require_manager_or_admin),
]

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "/claims",
    response_model=ClaimAnalyticsResponse,
)
def get_claim_analytics_endpoint(
    db: DatabaseSession,
    _: ManagerOrAdminUser,
    sla_days: int = Query(
        default=5,
        ge=1,
        le=365,
    ),
) -> dict:
    return get_claim_analytics(
        db=db,
        sla_days=sla_days,
    )