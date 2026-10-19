"""
router.py (claims module)
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.users.models import User
from src.auth.dependencies import get_current_user, require_role
from src.claims.schemas import (
    ClaimCreate,
    ClaimResponse,
    ClaimStatusUpdate,
    ClaimNoteResponse,
)
from src.claims import service

router = APIRouter(prefix="/api/v1/claims", tags=["claims"])


@router.post("", response_model=ClaimResponse, status_code=201)
def create_claim(
    payload: ClaimCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # FR-003: any authorized user
):
    return service.create_claim(db, payload, current_user)


@router.get("", response_model=list[ClaimResponse])
def list_claims(
    policy_number: Optional[str] = Query(None),
    claimant_name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_claims(
        db,
        current_user,
        policy_number=policy_number,
        claimant_name=claimant_name,
        status_filter=status,
    )


@router.get("/{claim_id}", response_model=ClaimResponse)
def get_claim(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_claim_by_id(db, claim_id, current_user)


@router.patch("/{claim_id}/status", response_model=ClaimResponse)
def update_claim_status(
    claim_id: str,
    payload: ClaimStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["adjuster", "manager", "admin"])),
):
    return service.update_claim_status(db, claim_id, payload, current_user)


@router.get("/{claim_id}/notes", response_model=list[ClaimNoteResponse])
def get_claim_notes(
    claim_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_claim_notes(db, claim_id, current_user)