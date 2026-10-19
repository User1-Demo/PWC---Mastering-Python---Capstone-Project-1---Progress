"""
router.py (documents module)

Purpose: Expose document upload/list/deactivate endpoints.
BR-001: Only Admin can upload/manage documents.
"""

from fastapi import APIRouter, Depends, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from typing import Optional

from src.database import get_db
from src.users.models import User
from src.auth.dependencies import get_current_user, require_role
from src.documents.schemas import DocumentResponse
from src.documents import service

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
def upload_document(
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.upload_document(db, title, file, current_user)


@router.get("", response_model=list[DocumentResponse])
def list_documents(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.list_documents(db, status_filter=status)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.get_document_by_id(db, document_id)


@router.patch("/{document_id}/deactivate", response_model=DocumentResponse)
def deactivate_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.set_document_status(db, document_id, "deactivated")


@router.patch("/{document_id}/activate", response_model=DocumentResponse)
def activate_document(
    document_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin"])),
):
    return service.set_document_status(db, document_id, "active")