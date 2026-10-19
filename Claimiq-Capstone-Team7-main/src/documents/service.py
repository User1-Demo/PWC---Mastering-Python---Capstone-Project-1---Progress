"""
service.py (documents module)

Purpose: Business logic for document upload/list/deactivate.
File storage is LOCAL DISK for now (data/documents/ folder) - this
is intentionally abstracted behind this service layer so swapping to
Azure Blob Storage later only requires changing THIS file, not the
router or any other module.
"""

import os
import shutil
import uuid
from pathlib import Path
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.documents.models import Document
from src.users.models import User
from src.audit.service import log_action
from src.ai_rag.document_processor import process_document
from src.ai_rag.vector_store import delete_chunks_by_document_id

# Local storage root - will become a Blob Storage container reference later
STORAGE_ROOT = Path("data/documents")


def save_file_to_storage(file: UploadFile, document_id: uuid.UUID) -> str:
    """
    Saves the uploaded file to local disk under a folder named after
    the document's own id (avoids filename collisions between uploads).
    Returns the relative file path to store in the database.
    """
    doc_folder = STORAGE_ROOT / str(document_id)
    doc_folder.mkdir(parents=True, exist_ok=True)

    file_path = doc_folder / file.filename

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return str(file_path)


def upload_document(db: Session, title: str, file: UploadFile, current_user: User) -> Document:
    allowed_extensions = {".pdf", ".docx", ".txt"}
    file_ext = os.path.splitext(file.filename)[1].lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported file type '{file_ext}'. Allowed: {allowed_extensions}",
        )

    # Create the DB record first (so we have an id to name the folder after)
    new_document = Document(
        title=title,
        file_path="",  # placeholder, filled in right after
        uploaded_by=current_user.id,
        status="active",
    )
    db.add(new_document)
    db.commit()
    db.refresh(new_document)

    # Now save the actual file, using the generated id
    saved_path = save_file_to_storage(file, new_document.id)

    new_document.file_path = saved_path
    db.commit()
    db.refresh(new_document)

    # Automatically chunk + embed the document into the vector store
    try:
        num_chunks = process_document(
            document_id=str(new_document.id),
            title=new_document.title,
            file_path=new_document.file_path,
        )
    except Exception as e:
        # Don't fail the whole upload if ingestion has an issue - the
        # document record still exists; log and handle reprocessing separately
        print(f"⚠️ Ingestion failed for document {new_document.id}: {e}")

    # Log the document upload action
    log_action(
        db,
        actor_id=current_user.id,
        action="document_uploaded",
        entity_type="document",
        entity_id=new_document.id,
        metadata={"title": title, "file_path": saved_path},
    )

    return new_document


def get_document_by_id(db: Session, document_id: str) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    return document


def list_documents(db: Session, status_filter: str | None = None) -> list[Document]:
    query = db.query(Document)
    if status_filter:
        query = query.filter(Document.status == status_filter)
    return query.order_by(Document.uploaded_at.desc()).all()


def set_document_status(db: Session, document_id: str, new_status: str) -> Document:
    """
    BR-006: Deactivated documents must not be used in future AI responses.
    This function just flips the flag - the AI/RAG retrieval logic
    (built later) will check this status before using any document's
    chunks in a response.
    """
    document = get_document_by_id(db, document_id)
    document.status = new_status
    db.commit()
    log_action(
        db,
        actor_id=document.uploaded_by,
        action=f"document_{new_status}",  # "document_active" or "document_deactivated"
        entity_type="document",
        entity_id=document.id,
        metadata={"new_status": new_status},
    )
    db.refresh(document)
    if new_status == "deactivated":
        delete_chunks_by_document_id(document_id)
    return document