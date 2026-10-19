from datetime import datetime

from pydantic import BaseModel, ConfigDict

from claimiq.models.document import DocumentStatus


class DocumentResponse(BaseModel):
    id: int
    title: str
    file_name: str
    file_path: str
    document_type: str
    version: str
    status: DocumentStatus
    uploaded_by: int
    approved_at: datetime | None
    deactivated_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentChunkResponse(BaseModel):
    id: int
    document_id: int
    chunk_index: int
    content: str
    page_number: int | None
    section_name: str | None
    vector_reference: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DocumentStatusUpdate(BaseModel):
    status: DocumentStatus