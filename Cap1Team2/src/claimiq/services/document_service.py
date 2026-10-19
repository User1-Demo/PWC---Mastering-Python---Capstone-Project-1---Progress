from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from claimiq.core.settings import get_settings
from claimiq.models.document import Document, DocumentStatus
from claimiq.schemas.document import DocumentStatusUpdate
from claimiq.services.audit_service import create_audit_log

ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".txt",
}


def validate_document_file(
    file_name: str,
    file_size: int,
) -> str:
    """Validate file extension and size, returning the extension."""

    settings = get_settings()
    extension = Path(file_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise ValueError(
            f"Unsupported file type. Allowed types: {allowed}",
        )

    max_size = settings.max_upload_size_mb * 1024 * 1024

    if file_size > max_size:
        raise ValueError(
            f"File size cannot exceed "
            f"{settings.max_upload_size_mb} MB",
        )

    return extension


def create_document(
    db: Session,
    *,
    file: UploadFile,
    title: str,
    document_type: str,
    version: str,
    uploaded_by: int,
) -> Document:
    """Store an uploaded document and create its database record."""

    if not file.filename:
        raise ValueError("A file name is required")

    file_content = file.file.read()
    extension = validate_document_file(
        file_name=file.filename,
        file_size=len(file_content),
    )

    settings = get_settings()
    storage_directory = Path(settings.upload_directory)
    storage_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    stored_file_name = f"{uuid4().hex}{extension}"
    stored_file_path = storage_directory / stored_file_name

    stored_file_path.write_bytes(file_content)

    document = Document(
        title=title,
        file_name=file.filename,
        file_path=str(stored_file_path),
        document_type=document_type,
        version=version,
        status=DocumentStatus.UPLOADED,
        uploaded_by=uploaded_by,
    )

    try:
        db.add(document)
        db.commit()
        db.refresh(document)
    except Exception:
        db.rollback()

        if stored_file_path.exists():
            stored_file_path.unlink()

        raise

    return document


def update_document_status(
    db: Session,
    *,
    document: Document,
    status_data: DocumentStatusUpdate,
) -> Document:
    """Update the status of a document."""

    document.status = status_data.status

    db.commit()
    db.refresh(document)

    return document


VALID_DOCUMENT_STATUS_TRANSITIONS: dict[
    DocumentStatus,
    set[DocumentStatus],
] = {
    DocumentStatus.UPLOADED: {
        DocumentStatus.PROCESSING,
        DocumentStatus.APPROVED,
    },
    DocumentStatus.PROCESSING: {
        DocumentStatus.APPROVED,
        DocumentStatus.FAILED,
    },
    DocumentStatus.APPROVED: {
        DocumentStatus.INACTIVE,
    },
    DocumentStatus.INACTIVE: set(),
    DocumentStatus.FAILED: set(),
}


def get_documents(
    db: Session,
    *,
    skip: int = 0,
    limit: int = 100,
) -> list[Document]:
    """Return documents using pagination."""

    statement = (
        select(Document)
        .order_by(
            Document.created_at.desc(),
            Document.id.desc(),
        )
        .offset(skip)
        .limit(limit)
    )

    return list(db.scalars(statement).all())


def get_document_by_id(
    db: Session,
    document_id: int,
) -> Document | None:
    """Return a document by ID."""
    return db.get(Document, document_id)


def validate_document_status_transition(
    current_status: DocumentStatus,
    new_status: DocumentStatus,
) -> None:
    """Validate whether a document status change is allowed."""

    if current_status == new_status:
        raise ValueError(
            "Document is already in the requested status",
        )

    allowed_statuses = VALID_DOCUMENT_STATUS_TRANSITIONS.get(
        current_status,
        set(),
    )

    if new_status not in allowed_statuses:
        raise ValueError(
            "Invalid document status transition: "
            f"{current_status.value} to {new_status.value}",
        )


def change_document_status(
    db: Session,
    *,
    document: Document,
    new_status: DocumentStatus,
    actor_user_id: int,
) -> Document:
    """Change document status and create an audit record."""

    previous_status = document.status

    validate_document_status_transition(
        current_status=previous_status,
        new_status=new_status,
    )

    document.status = new_status

    if new_status == DocumentStatus.APPROVED:
        document.approved_at = datetime.now(UTC)

    if new_status == DocumentStatus.INACTIVE:
        document.deactivated_at = datetime.now(UTC)

    db.commit()
    db.refresh(document)

    if new_status == DocumentStatus.APPROVED:
        action = "DOCUMENT_APPROVED"
    elif new_status == DocumentStatus.INACTIVE:
        action = "DOCUMENT_DEACTIVATED"
    else:
        action = "DOCUMENT_STATUS_CHANGED"

    create_audit_log(
        db=db,
        action=action,
        user_id=actor_user_id,
        entity_type="Document",
        entity_id=document.id,
        metadata={
            "previous_status": previous_status.value,
            "new_status": new_status.value,
        },
    )

    return document