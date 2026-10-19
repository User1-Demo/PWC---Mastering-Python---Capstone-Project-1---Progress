import os
import re
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from src.app.db.models import Document, DocumentChunk, DocumentStatus

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "application/pdf",
}


def save_uploaded_file(file: UploadFile) -> tuple[str, str]:
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only TXT and PDF files are supported",
        )

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    file_path = UPLOAD_DIR / unique_name

    with open(file_path, "wb") as f:
        f.write(file.file.read())

    return str(file_path), file.filename


def extract_text_from_txt(file_path: str) -> str:
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text_from_pdf(file_path: str) -> str:
    try:
        import PyPDF2
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="PyPDF2 is not installed",
        )

    text_parts = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text() or ""
            text_parts.append(page_text)

    return "\n".join(text_parts)


def extract_document_text(file_path: str, content_type: str | None) -> str:
    if content_type == "text/plain":
        return extract_text_from_txt(file_path)

    if content_type == "application/pdf":
        return extract_text_from_pdf(file_path)

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Unsupported file type for text extraction",
    )


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return text


def chunk_text(
    text: str,
    chunk_size: int = 800,
    chunk_overlap: int = 100,
) -> list[str]:
    text = clean_text(text)

    if not text:
        return []

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def create_document_with_chunks(
    db: Session,
    *,
    title: str,
    file: UploadFile,
    uploaded_by: int,
) -> Document:
    file_path, original_filename = save_uploaded_file(file)

    document = Document(
        title=title,
        filename=original_filename,
        file_path=file_path,
        content_type=file.content_type,
        uploaded_by=uploaded_by,
        status=DocumentStatus.ACTIVE,
    )
    db.add(document)
    db.flush()

    extracted_text = extract_document_text(file_path, file.content_type)
    chunks = chunk_text(extracted_text)

    for index, chunk in enumerate(chunks):
        db.add(
            DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                chunk_text=chunk,
                section_ref=f"chunk-{index + 1}",
                embedding_status="pending",
            )
        )

    db.commit()
    db.refresh(document)
    return document