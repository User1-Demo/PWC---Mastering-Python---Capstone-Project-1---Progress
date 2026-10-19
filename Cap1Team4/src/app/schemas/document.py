import uuid
from datetime import datetime

from pydantic import BaseModel

from app.models.enums import DocumentStatus, DocumentType, PolicyType
from app.schemas.common import ORMModel


class DocumentOut(ORMModel):
    id: uuid.UUID
    title: str
    original_filename: str
    file_hash: str
    mime_type: str
    size_bytes: int
    doc_type: DocumentType
    applies_to: PolicyType | None
    version: str | None
    status: DocumentStatus
    is_active: bool
    chunk_count: int
    uploaded_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class DocumentUploadFields(BaseModel):
    title: str
    doc_type: DocumentType
    applies_to: PolicyType | None = None
    version: str | None = None


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus
