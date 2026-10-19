from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies.auth import require_roles
from src.common.enums import UserRole
from src.db.session import get_db
from src.models.user import User
from src.schemas.claim import (
    ClaimAssignment,
    ClaimCreate,
    ClaimResponse,
    ClaimUpdate,
)
from src.services.claim_service import ClaimService

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claims"],
)


@router.post(
    "/",
    response_model=ClaimResponse,
)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.manager,
            UserRole.adjuster,
            UserRole.support,
        )
    ),
):
    return ClaimService.create_claim(
        db,
        payload,
    )


@router.get(
    "/",
    response_model=list[ClaimResponse],
)
def get_claims(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.manager,
            UserRole.adjuster,
            UserRole.support,
        )
    ),
):
    return ClaimService.get_claims(
        db,
        current_user,
    )


@router.patch(
    "/{claim_id}/assign",
    response_model=ClaimResponse,
)
def assign_claim(
    claim_id: int,
    payload: ClaimAssignment,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.manager,
        )
    ),
):
    return ClaimService.assign_claim(
        db=db,
        claim_id=claim_id,
        assigned_adjuster_id=payload.assigned_adjuster_id,
    )


@router.get(
    "/{claim_id}",
    response_model=ClaimResponse,
)
def get_claim(
    claim_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.manager,
            UserRole.adjuster,
            UserRole.support,
        )
    ),
):
    return ClaimService.get_claim(
        db,
        claim_id,
        current_user,
    )


@router.put(
    "/{claim_id}",
    response_model=ClaimResponse,
)
def update_claim(
    claim_id: int,
    payload: ClaimUpdate,
    db: Session = Depends(get_db),
):
    return ClaimService.update_claim(
        db,
        claim_id,
        payload,
    )


@router.delete(
    "/{claim_id}",
)
def delete_claim(
    claim_id: int,
    db: Session = Depends(get_db),
):
    return ClaimService.delete_claim(
        db,
        claim_id,
    )
