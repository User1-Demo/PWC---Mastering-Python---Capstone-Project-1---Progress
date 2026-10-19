from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api.dependencies.auth import require_roles
from src.common.enums import UserRole
from src.db.session import get_db
from src.models.user import User
from src.schemas.policy import PolicyCreate, PolicyRead, PolicyUpdate
from src.services.policy_service import *

router = APIRouter(
    prefix="/api/v1/policies",
    tags=["Policies"],
)


@router.post("", response_model=PolicyRead)
def create_new_policy(
    payload: PolicyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin, UserRole.manager)),
):
    return create_policy(payload, db)


@router.get("", response_model=list[PolicyRead])
def list_policies(
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
    return get_policies(db)


@router.get("/{policy_id}", response_model=PolicyRead)
def get_policy(
    policy_id: int,
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
    return get_policy_by_id(policy_id, db)


@router.put("/{policy_id}", response_model=PolicyRead)
def update_existing_policy(
    policy_id: int,
    payload: PolicyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(
            UserRole.admin,
            UserRole.manager,
        )
    ),
):
    return update_policy(policy_id, payload, db)


@router.delete("/{policy_id}")
def remove_policy(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return delete_policy(policy_id, db)
