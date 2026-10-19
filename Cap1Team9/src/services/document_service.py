from fastapi import HTTPException

from src.models.document import Document


def create_document(
    file_name: str,
    content_type: str,
    file_path: str,
    uploaded_by: int,
    db,
):
    document = Document(
        file_name=file_name,
        content_type=content_type,
        file_path=file_path,
        uploaded_by=uploaded_by,
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def get_documents(db):
    return db.query(Document).all()


def get_document_by_id(document_id: int, db):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    return document


def update_document_status(
    document_id: int,
    is_active: bool,
    db,
):
    document = get_document_by_id(document_id, db)

    document.is_active = is_active

    db.commit()
    db.refresh(document)

    return document
