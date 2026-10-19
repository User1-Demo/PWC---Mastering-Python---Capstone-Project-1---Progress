from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from claimiq.core.permissions import require_admin
from claimiq.db.database import get_db
from claimiq.models.document import Document
from claimiq.models.user import User
from claimiq.schemas.document import (
    DocumentResponse,
    DocumentStatusUpdate,
)
from claimiq.services.document_processing_service import (
    process_document,
)
from claimiq.services.document_service import (
    change_document_status,
    create_document,
    get_document_by_id,
    get_documents,
)

router = APIRouter(
    prefix="/api/v1/documents",
    tags=["Documents"],
)


AdminUser = Annotated[
    User,
    Depends(require_admin),
]

DatabaseSession = Annotated[
    Session,
    Depends(get_db),
]


@router.post(
    "",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
)
def upload_document_endpoint(
    title: Annotated[str, Form()],
    document_type: Annotated[str, Form()],
    file: Annotated[UploadFile, File()],
    db: DatabaseSession,
    current_user: AdminUser,
    version: Annotated[str, Form()] = "1.0",
) -> Document:
    """Upload a document as an administrator."""

    try:
        return create_document(
            db=db,
            file=file,
            title=title,
            document_type=document_type,
            version=version,
            uploaded_by=current_user.id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.get(
    "",
    response_model=list[DocumentResponse],
)
def list_documents_endpoint(
    db: DatabaseSession,
    _: AdminUser,
    skip: int = Query(
        default=0,
        ge=0,
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=100,
    ),
) -> list[Document]:
    """Return documents with pagination."""

    return get_documents(
        db=db,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
)
def get_document_endpoint(
    document_id: int,
    db: DatabaseSession,
    _: AdminUser,
) -> Document:
    """Return one document by ID."""

    document = get_document_by_id(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return document


@router.post(
    "/{document_id}/process",
    response_model=DocumentResponse,
)
def process_document_endpoint(
    document_id: int,
    db: DatabaseSession,
    current_user: AdminUser,
) -> Document:
    """Extract and chunk a document."""

    try:
        return process_document(
            db=db,
            document_id=document_id,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        message = str(exc)

        if message == "Document not found":
            response_status = status.HTTP_404_NOT_FOUND
        else:
            response_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc


@router.patch(
    "/{document_id}/status",
    response_model=DocumentResponse,
)
def change_document_status_endpoint(
    document_id: int,
    status_data: DocumentStatusUpdate,
    db: DatabaseSession,
    current_user: AdminUser,
) -> Document:
    """Approve, deactivate, or change a document status."""

    document = get_document_by_id(
        db=db,
        document_id=document_id,
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    try:
        return change_document_status(
            db=db,
            document=document,
            new_status=status_data.status,
            actor_user_id=current_user.id,
        )
    except ValueError as exc:
        message = str(exc)

        if message.startswith("Invalid document status"):
            response_status = status.HTTP_409_CONFLICT
        else:
            response_status = status.HTTP_400_BAD_REQUEST

        raise HTTPException(
            status_code=response_status,
            detail=message,
        ) from exc