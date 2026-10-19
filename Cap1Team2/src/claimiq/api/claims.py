from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from claimiq.core.permissions import require_claims_staff
from claimiq.db.database import get_db
from claimiq.models.claim import Claim
from claimiq.models.user import User
from claimiq.schemas.claim import (
    ClaimCreate,
    ClaimResponse,
    ClaimStatusUpdate,
    ClaimUpdate,
)
from claimiq.schemas.claim_status_history import (
    ClaimStatusHistoryResponse,
)
from claimiq.services.claim_history_service import (
    get_claim_status_history,
)
from claimiq.services.claim_service import (
    create_claim,
    get_claim_by_id,
    get_claims,
    update_claim,
)
from claimiq.services.claim_status_service import update_claim_status

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claims"],
)


ClaimsStaffUser = Annotated[
    User,
    Depends(require_claims_staff),
]


@router.post(
    "",
    response_model=ClaimResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_endpoint(
    claim_data: ClaimCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: ClaimsStaffUser,
) -> Claim:
    try:
        return create_claim(
            db=db,
            claim_data=claim_data,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[ClaimResponse],
)
def list_claims_endpoint(
    db: Annotated[Session, Depends(get_db)],
    _: ClaimsStaffUser,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
) -> list[Claim]:
    return get_claims(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
)
def get_claim_endpoint(
    claim_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: ClaimsStaffUser,
) -> Claim:
    claim = get_claim_by_id(
        db=db,
        claim_id=claim_id,
    )

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    return claim


@router.get(
    "/{claim_id}/history",
    response_model=list[ClaimStatusHistoryResponse],
)
def get_claim_history_endpoint(
    claim_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: ClaimsStaffUser,
) -> list:
    try:
        return get_claim_status_history(
            db=db,
            claim_id=claim_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.patch(
    "/{claim_id}/status",
    response_model=ClaimResponse,
)
def update_claim_status_endpoint(
    claim_id: int,
    status_data: ClaimStatusUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: ClaimsStaffUser,
) -> Claim:
    try:
        return update_claim_status(
            db=db,
            claim_id=claim_id,
            status_data=status_data,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Claim not found":
            response_status = status.HTTP_404_NOT_FOUND
        elif message.startswith("Invalid"):
            response_status = status.HTTP_409_CONFLICT
        else:
            response_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc



@router.patch(
    "/{claim_id}",
    response_model=ClaimResponse,
)
def update_claim_endpoint(
    claim_id: int,
    claim_data: ClaimUpdate,
    db: Annotated[Session, Depends(get_db)],
    current_user: ClaimsStaffUser,
) -> Claim:
    claim = get_claim_by_id(
        db=db,
        claim_id=claim_id,
    )

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Claim not found",
        )

    try:
        return update_claim(
            db=db,
            claim=claim,
            claim_data=claim_data,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc