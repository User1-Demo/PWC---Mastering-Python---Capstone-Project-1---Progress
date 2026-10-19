from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from src.app.core.security import get_current_user
from src.app.db.models import Document, DocumentStatus, User, UserRole
from src.app.db.session import get_db
from src.app.schemas.document import (
    DocumentDetailResponse,
    DocumentResponse,
    DocumentStatusUpdate,
)
from src.app.services.document_service import create_document_with_chunks
from src.app.services.audit import create_audit_log

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

DatabaseSession = Annotated[Session, Depends(get_db)]


def require_admin(current_user: User) -> None:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can manage documents",
        )


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
    title: str = Form(...),
    file: UploadFile = File(...),
):
    require_admin(current_user)

    document = create_document_with_chunks(
        db,
        title=title,
        file=file,
        uploaded_by=current_user.id,
    )

    create_audit_log(
        db,
        user_id=current_user.id,
        action="DOCUMENT_UPLOADED",
        entity_type="document",
        entity_id=document.id,
        details=f"Document uploaded: {document.filename}",
    )
    db.commit()

    return document


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents(
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    docs = db.scalars(
        select(Document).order_by(Document.created_at.desc())
    ).all()

    return docs


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
)
def get_document(
    document_id: int,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    document = db.execute(
        select(Document)
        .options(selectinload(Document.chunks))
        .where(Document.id == document_id)
    ).scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.patch(
    "/{document_id}/status",
    response_model=DocumentResponse,
)
def update_document_status(
    document_id: int,
    payload: DocumentStatusUpdate,
    db: DatabaseSession,
    current_user: User = Depends(get_current_user),
):
    require_admin(current_user)

    document = db.get(Document, document_id)

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    document.status = payload.status
    db.commit()
    db.refresh(document)

    create_audit_log(
        db,
        user_id=current_user.id,
        action="DOCUMENT_STATUS_UPDATED",
        entity_type="document",
        entity_id=document.id,
        details=f"Document status changed to {document.status.value}",
    )
    db.commit()

    return document