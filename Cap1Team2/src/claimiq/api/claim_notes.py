from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from claimiq.core.dependencies import CurrentUser
from claimiq.core.permissions import require_claims_staff
from claimiq.db.database import get_db
from claimiq.models.claim_note import ClaimNote
from claimiq.models.user import User
from claimiq.schemas.claim_note import (
    ClaimNoteCreate,
    ClaimNoteResponse,
)
from claimiq.services.claim_note_service import (
    create_claim_note,
    get_claim_notes,
)

router = APIRouter(
    prefix="/api/v1/claims",
    tags=["Claim Notes"],
)


ClaimsStaffUser = Annotated[
    User,
    Depends(require_claims_staff),
]


@router.post(
    "/{claim_id}/notes",
    response_model=ClaimNoteResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_claim_note_endpoint(
    claim_id: int,
    note_data: ClaimNoteCreate,
    db: Annotated[Session, Depends(get_db)],
    current_user: CurrentUser,
    _: ClaimsStaffUser,
) -> ClaimNote:
    try:
        return create_claim_note(
            db=db,
            claim_id=claim_id,
            author_id=current_user.id,
            note_data=note_data,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/{claim_id}/notes",
    response_model=list[ClaimNoteResponse],
)
def list_claim_notes_endpoint(
    claim_id: int,
    db: Annotated[Session, Depends(get_db)],
    _: ClaimsStaffUser,
) -> list[ClaimNote]:
    return get_claim_notes(
        db=db,
        claim_id=claim_id,
    )