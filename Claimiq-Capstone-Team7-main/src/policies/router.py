"""
router.py (policies module)

Purpose: Expose Policy CRUD endpoints. Creation is Admin-only
(BR-001: only Admin manages core reference data).
Reading policies is open to any authenticated user, since
Adjusters/Support Agents need to view policy details tied to claims.
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.users.models import User
from src.auth.dependencies import get_current_user, require_role
from src.policies.schemas import PolicyCreate, PolicyResponse, PolicyUpdateStatus
from src.policies import service

router = APIRouter(prefix="/api/v1/policies", tags=["policies"])


@router.post("", response_model=PolicyResponse, status_code=201)
def create_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.create_policy(db, payload)


@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(
    policy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_policy_by_id(db, policy_id)


@router.get("", response_model=list[PolicyResponse])
def list_policies(
    region: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_policies(db, region=region, status_filter=status, policy_type=type)


@router.patch("/{policy_id}/status", response_model=PolicyResponse)
def update_policy_status(
    policy_id: str,
    payload: PolicyUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.update_policy_status(db, policy_id, payload.status.value)