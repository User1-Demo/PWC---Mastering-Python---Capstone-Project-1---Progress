from pathlib import Path

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)

from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..audit_service import write_audit_log
from ..auth import get_current_user
from ..config import settings
from ..database import get_db
from ..dependencies import officer_or_admin
from ..file_utils import (
    delete_upload,
    save_upload,
)
from ..vector_store import (
    delete_policy_document_vectors,
)


router = APIRouter(
    tags=["Documents"]
)


def verify_policy_access(
    db: Session,
    policy_id: int,
    current_user: models.User
):
    policy = db.get(
        models.Policy,
        policy_id
    )

    if not policy:
        raise HTTPException(
            status_code=404,
            detail="Policy not found"
        )

    if (
        current_user.role == models.UserRole.user
        and policy.owner_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Policy access denied"
        )

    return policy


def verify_claim_access(
    db: Session,
    claim_id: int,
    current_user: models.User
):
    claim = db.get(
        models.Claim,
        claim_id
    )

    if not claim:
        raise HTTPException(
            status_code=404,
            detail="Claim not found"
        )

    if (
        current_user.role == models.UserRole.user
        and claim.created_by_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Claim access denied"
        )

    return claim


@router.post(
    "/policies/{policy_id}/documents",
    response_model=schemas.DocumentRead,
    status_code=status.HTTP_201_CREATED
)
def upload_policy_document(
    policy_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        officer_or_admin
    )
):
    verify_policy_access(
        db,
        policy_id,
        current_user
    )

    stored_filename, file_size = save_upload(
        file,
        "policies"
    )

    document = models.PolicyDocument(
        policy_id=policy_id,
        original_filename=(
            file.filename or "document"
        ),
        stored_filename=stored_filename,
        content_type=(
            file.content_type
            or "application/octet-stream"
        ),
        file_size=file_size,
        uploaded_by_id=current_user.id,
        is_active=True
    )

    db.add(document)
    db.flush()

    write_audit_log(
        db=db,
        user_id=current_user.id,
        action="policy_document_uploaded",
        entity_type="policy_document",
        entity_id=document.id,
        details={
            "policy_id": policy_id,
            "filename": document.original_filename,
            "content_type": document.content_type,
            "file_size": document.file_size
        }
    )

    db.commit()
    db.refresh(document)

    return document


@router.get(
    "/policies/{policy_id}/documents",
    response_model=list[schemas.DocumentRead]
)
def list_policy_documents(
    policy_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    )
):
    verify_policy_access(
        db,
        policy_id,
        current_user
    )

    query = (
        db.query(models.PolicyDocument)
        .filter(
            models.PolicyDocument.policy_id
            == policy_id
        )
    )

    if current_user.role == models.UserRole.user:
        query = query.filter(
            models.PolicyDocument.is_active.is_(True)
        )

    return (
        query
        .order_by(
            models.PolicyDocument.id.desc()
        )
        .all()
    )


@router.get(
    "/claim-documents/{document_id}/download"
)
def download_claim_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(
        get_current_user
    )
):
    document = db.get(
        models.ClaimDocument,
        document_id
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Claim document not found"
        )

    verify_claim_access(
        db,
        document.claim_id,
        current_user
    )

    if (
        not document.is_active
        and current_user.role == models.UserRole.user
    ):
        raise HTTPException(
            status_code=403,
            detail="Claim document is inactive"
        )

    file_path = (
        Path(settings.upload_dir)
        / "claims"
        / document.stored_filename
    )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="Stored file not found"
        )

    return FileResponse(
        path=file_path,
        media_type=document.content_type,
        filename=document.original_filename
    ) 