from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.app.db.models import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    title: str
    filename: str
    file_path: str
    content_type: str | None
    uploaded_by: int
    status: DocumentStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    chunk_text: str
    section_ref: str | None
    embedding_status: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentDetailResponse(DocumentResponse):
    chunks: list[DocumentChunkResponse] = []

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus