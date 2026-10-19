from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.api.dependencies.auth import get_current_user, require_roles
from src.common.enums import UserRole
from src.db.session import get_db
from src.models.user import User
from src.schemas.document import DocumentResponse, DocumentStatusUpdate
from src.services.document_service import (
    create_document,
    get_document_by_id,
    get_documents,
    update_document_status,
)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="File name is required",
        )

    allowed_content_types = {
        "application/pdf",
    }

    if file.content_type not in allowed_content_types:
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    unique_filename = f"{uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename

    content = await file.read()

    with open(file_path, "wb") as destination:
        destination.write(content)

    return create_document(
        file_name=file.filename,
        content_type=file.content_type,
        file_path=str(file_path),
        uploaded_by=current_user.id,
        db=db,
    )


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return get_documents(db)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return get_document_by_id(document_id, db)


@router.patch("/{document_id}/status", response_model=DocumentResponse)
def change_document_status(
    document_id: int,
    payload: DocumentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.admin)),
):
    return update_document_status(
        document_id,
        payload.is_active,
        db,
    )
