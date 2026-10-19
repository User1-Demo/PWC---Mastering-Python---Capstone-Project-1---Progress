from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.models.claim import Claim
from claimiq.models.claim_note import ClaimNote
from claimiq.schemas.claim_note import ClaimNoteCreate
from claimiq.services.audit_service import create_audit_log


def get_claim_notes(
    db: Session,
    claim_id: int,
) -> list[ClaimNote]:
    """Return all notes for a claim."""
    statement = (
        select(ClaimNote)
        .where(ClaimNote.claim_id == claim_id)
        .order_by(
            ClaimNote.created_at,
            ClaimNote.id,
        )
    )

    return list(db.scalars(statement).all())


def create_claim_note(
    db: Session,
    claim_id: int,
    author_id: int,
    note_data: ClaimNoteCreate,
) -> ClaimNote:
    """Create a note for an existing claim and audit the action."""
    claim = db.get(Claim, claim_id)

    if claim is None:
        raise ValueError("Claim not found")

    note = ClaimNote(
        claim_id=claim_id,
        author_id=author_id,
        note_text=note_data.note_text,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    create_audit_log(
        db=db,
        action="CLAIM_NOTE_CREATED",
        user_id=author_id,
        entity_type="ClaimNote",
        entity_id=note.id,
        metadata={
            "claim_id": claim_id,
        },
    )

    return note