import uuid

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.db.session import get_db
from app.models.enums import UserRole
from app.models.enums import PolicyType
from app.models.policy import Policy
from app.models.user import Region, User
from app.schemas.policy import PolicyCreate, PolicyOut, PolicyStatusUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/policies", tags=["policies"])
policy_admin = require_roles(UserRole.ADMIN, UserRole.CLAIMS_MANAGER)
authenticated = require_roles(
    UserRole.ADMIN,
    UserRole.CLAIMS_MANAGER,
    UserRole.CLAIMS_ADJUSTER,
    UserRole.SUPPORT_AGENT,
)


@router.post("", response_model=PolicyOut, status_code=201)
def create_policy(
    payload: PolicyCreate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(policy_admin),
) -> Policy:
    if db.scalar(select(Policy).where(Policy.policy_number == payload.policy_number)):
        raise BusinessRuleError("A policy with this policy number already exists")
    region = db.get(Region, payload.region_id)
    if region is None or not region.is_active:
        raise NotFoundError("Region not found")
    policy = Policy(**payload.model_dump())
    db.add(policy)
    db.flush()
    log_action(
        db,
        action="POLICY_CREATED",
        entity_type="policy",
        entity_id=str(policy.id),
        actor=actor,
        new={"policy_number": policy.policy_number, "policy_type": policy.policy_type.value},
        request=request,
    )
    db.commit()
    db.refresh(policy)
    return policy


@router.get("", response_model=list[PolicyOut])
def list_policies(
    policy_number: str | None = Query(default=None, max_length=50),
    policy_type: PolicyType | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> list[Policy]:
    query = select(Policy)
    if policy_number:
        query = query.where(Policy.policy_number.ilike(f"%{policy_number}%"))
    if policy_type:
        query = query.where(Policy.policy_type == policy_type)
    if actor.role in (UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT):
        query = query.where(Policy.region_id == actor.region_id)
    return list(db.scalars(query.order_by(Policy.created_at.desc())))


@router.get("/{policy_id}", response_model=PolicyOut)
def get_policy(
    policy_id: uuid.UUID,
    db: Session = Depends(get_db),
    actor: User = Depends(authenticated),
) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    if (
        actor.role in (UserRole.CLAIMS_ADJUSTER, UserRole.SUPPORT_AGENT)
        and policy.region_id != actor.region_id
    ):
        raise NotFoundError("Policy not found")
    return policy


@router.patch("/{policy_id}/status", response_model=PolicyOut)
def update_policy_status(
    policy_id: uuid.UUID,
    payload: PolicyStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    actor: User = Depends(policy_admin),
) -> Policy:
    policy = db.get(Policy, policy_id)
    if policy is None:
        raise NotFoundError("Policy not found")
    old_status = policy.status
    policy.status = payload.status
    log_action(
        db,
        action="POLICY_STATUS_CHANGED",
        entity_type="policy",
        entity_id=str(policy.id),
        actor=actor,
        old={"status": old_status.value},
        new={"status": policy.status.value},
        request=request,
    )
    db.commit()
    db.refresh(policy)
    return policy
