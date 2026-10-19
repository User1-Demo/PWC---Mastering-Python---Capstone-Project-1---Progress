from pathlib import Path

from sqlalchemy import delete
from sqlalchemy.orm import Session

from claimiq.models.document import Document, DocumentStatus
from claimiq.models.document_chunk import DocumentChunk
from claimiq.services.audit_service import create_audit_log
from claimiq.services.text_chunking_service import chunk_text
from claimiq.services.text_extraction_service import extract_text


def process_document(
    db: Session,
    *,
    document_id: int,
    actor_user_id: int,
    chunk_size: int = 100,
    overlap: int = 20,
) -> Document:
    """Extract, chunk, and store a document's text."""

    document = db.get(Document, document_id)

    if document is None:
        raise ValueError("Document not found")

    if document.status not in {
        DocumentStatus.UPLOADED,
        DocumentStatus.FAILED,
    }:
        raise ValueError(
            "Only uploaded or failed documents can be processed",
        )

    document.status = DocumentStatus.PROCESSING
    db.commit()
    db.refresh(document)

    try:
        file_path = Path(document.file_path)
        extracted_text = extract_text(file_path)

        chunks = chunk_text(
            extracted_text,
            chunk_size=chunk_size,
            overlap=overlap,
        )

        if not chunks:
            raise ValueError(
                "No text chunks were generated",
            )

        db.execute(
            delete(DocumentChunk).where(
                DocumentChunk.document_id == document.id,
            ),
        )

        for index, content in enumerate(chunks):
            document_chunk = DocumentChunk(
                document_id=document.id,
                chunk_index=index,
                content=content,
                page_number=None,
                section_name=None,
                vector_reference=None,
            )

            db.add(document_chunk)

        document.status = DocumentStatus.APPROVED
        db.commit()
        db.refresh(document)

        create_audit_log(
            db=db,
            action="DOCUMENT_PROCESSED",
            user_id=actor_user_id,
            entity_type="Document",
            entity_id=document.id,
            metadata={
                "chunk_count": len(chunks),
                "status": DocumentStatus.APPROVED.value,
            },
        )

        return document

    except Exception as exc:
        db.rollback()

        failed_document = db.get(
            Document,
            document_id,
        )

        if failed_document is not None:
            failed_document.status = DocumentStatus.FAILED
            db.commit()

            create_audit_log(
                db=db,
                action="DOCUMENT_PROCESSING_FAILED",
                user_id=actor_user_id,
                entity_type="Document",
                entity_id=document_id,
                metadata={
                    "error": str(exc)[:500],
                    "status": DocumentStatus.FAILED.value,
                },
            )

        raise ValueError(
            f"Document processing failed: {exc}",
        ) from exc