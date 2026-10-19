import hashlib
import io
import uuid
from datetime import UTC, datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.core.config import settings
from app.core.exceptions import BusinessRuleError, NotFoundError
from app.db.session import get_db
from app.models.document import Document, DocumentChunk
from app.models.enums import DocumentStatus, DocumentType, PolicyType, UserRole
from app.models.user import User
from app.rag.chunker import chunk_pages
from app.schemas.document import DocumentOut, DocumentStatusUpdate
from app.services.audit_service import log_action

router = APIRouter(prefix="/documents", tags=["documents"])
admin_only = require_roles(UserRole.ADMIN)
storage_dir = Path(settings.DOCUMENT_STORAGE_DIR)
_SUPPORTED_EXTENSIONS = {".txt", ".md", ".pdf"}


def _extract_pages(content: bytes, extension: str) -> list[tuple[int | None, str]]:
    if extension == ".pdf":
        try:
            reader = PdfReader(io.BytesIO(content), strict=False)
            if reader.is_encrypted:
                raise BusinessRuleError("Encrypted PDF documents are not supported")
            pages = [
                (index + 1, page.extract_text() or "")
                for index, page in enumerate(reader.pages)
            ]
        except (PdfReadError, ValueError) as exc:
            raise BusinessRuleError("The uploaded PDF could not be read") from exc
    else:
        try:
            pages = [(None, content.decode("utf-8-sig"))]
        except UnicodeDecodeError as exc:
            raise BusinessRuleError("Text documents must use UTF-8 encoding") from exc
    if not any(text.strip() for _, text in pages):
        raise BusinessRuleError("The document contains no extractable text")
    return pages


@router.post("", response_model=DocumentOut, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    title: str = Form("", max_length=255),
    doc_type: DocumentType = Form(...),
    applies_to: PolicyType | None = Form(None),
    version: str | None = Form(None, max_length=50),
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> Document:
    extension = Path(file.filename or "").suffix.lower()
    if extension not in _SUPPORTED_EXTENSIONS:
        raise BusinessRuleError("Only UTF-8 text, Markdown, and text-based PDF files are supported")

    content = await file.read(settings.MAX_UPLOAD_BYTES + 1)
    if not content:
        raise BusinessRuleError("Uploaded document is empty")
    if len(content) > settings.MAX_UPLOAD_BYTES:
        raise BusinessRuleError("Uploaded document exceeds the configured size limit")

    file_hash = hashlib.sha256(content).hexdigest()
    if db.scalar(select(Document).where(Document.file_hash == file_hash)):
        raise BusinessRuleError("A document with this content has already been uploaded")

    extracted_pages = _extract_pages(content, extension)
    indexed_chunks = chunk_pages(
        extracted_pages,
        chunk_size=settings.RAG_CHUNK_SIZE,
        overlap=settings.RAG_CHUNK_OVERLAP,
    )
    if not indexed_chunks:
        raise BusinessRuleError("The document contains no extractable text")

    storage_dir.mkdir(parents=True, exist_ok=True)
    path = storage_dir / f"{uuid.uuid4().hex}{extension}"
    path.write_bytes(content)
    try:
        document = Document(
            title=title.strip() or (file.filename or "Untitled document"),
            original_filename=Path(file.filename or "upload").name[:255],
            storage_path=str(path),
            file_hash=file_hash,
            mime_type=file.content_type or "application/octet-stream",
            size_bytes=len(content),
            doc_type=doc_type,
            applies_to=applies_to,
            version=version,
            status=DocumentStatus.ACTIVE,
            is_active=True,
            uploaded_by=admin.id,
        )
        db.add(document)
        db.flush()
        for index, (text, heading, page_number) in enumerate(indexed_chunks):
            db.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=index,
                    content=text,
                    section_heading=heading,
                    page_number=page_number,
                    token_count=len(text.split()),
                    is_active=True,
                )
            )
        document.chunk_count = len(indexed_chunks)
        log_action(
            db,
            action="DOCUMENT_UPLOADED",
            entity_type="document",
            entity_id=str(document.id),
            actor=admin,
            new={"file_hash": file_hash, "size_bytes": len(content), "doc_type": doc_type.value},
            request=request,
        )
        db.commit()
        db.refresh(document)
        return document
    except SQLAlchemyError:
        db.rollback()
        path.unlink(missing_ok=True)
        raise


@router.get("", response_model=list[DocumentOut])
def list_documents(
    db: Session = Depends(get_db),
    _: User = Depends(admin_only),
) -> list[Document]:
    return list(db.scalars(select(Document).order_by(Document.created_at.desc())))


@router.patch("/{document_id}/status", response_model=DocumentOut)
def update_document_status(
    document_id: uuid.UUID,
    payload: DocumentStatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only),
) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise NotFoundError("Document not found")
    if payload.status not in (DocumentStatus.ACTIVE, DocumentStatus.INACTIVE):
        raise BusinessRuleError("Documents can only be activated or deactivated")

    old_status = document.status
    document.status = payload.status
    document.is_active = payload.status == DocumentStatus.ACTIVE
    document.deactivated_by = None if document.is_active else admin.id
    document.deactivated_at = None if document.is_active else datetime.now(UTC)
    for chunk in document.chunks:
        chunk.is_active = document.is_active
    log_action(
        db,
        action="DOCUMENT_ACTIVATED" if document.is_active else "DOCUMENT_DEACTIVATED",
        entity_type="document",
        entity_id=str(document.id),
        actor=admin,
        old={"status": old_status.value},
        new={"status": document.status.value},
        request=request,
    )
    db.commit()
    db.refresh(document)
    return document
