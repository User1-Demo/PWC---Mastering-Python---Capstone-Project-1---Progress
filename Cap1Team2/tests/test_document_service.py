from datetime import datetime
from unittest.mock import Mock

import pytest

from claimiq.models.document import Document, DocumentStatus
from claimiq.services.document_service import (
    change_document_status,
    validate_document_file,
    validate_document_status_transition,
)


def create_document(
    status: DocumentStatus = DocumentStatus.UPLOADED,
) -> Document:
    return Document(
        id=1,
        title="Vehicle Policy Manual",
        file_name="vehicle_policy.txt",
        file_path="storage/documents/test-file.txt",
        document_type="POLICY_MANUAL",
        version="1.0",
        status=status,
        uploaded_by=1,
    )


@pytest.mark.parametrize(
    "file_name",
    [
        "policy.pdf",
        "policy.docx",
        "policy.txt",
    ],
)
def test_allowed_document_extensions(file_name: str) -> None:
    extension = validate_document_file(
        file_name=file_name,
        file_size=1024,
    )

    assert extension in {".pdf", ".docx", ".txt"}


def test_unsupported_document_extension_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="Unsupported file type",
    ):
        validate_document_file(
            file_name="policy.exe",
            file_size=1024,
        )


def test_uploaded_document_can_be_approved() -> None:
    db = Mock()
    document = create_document(DocumentStatus.UPLOADED)

    result = change_document_status(
        db=db,
        document=document,
        new_status=DocumentStatus.APPROVED,
        actor_user_id=1,
    )

    assert result.status == DocumentStatus.APPROVED
    assert isinstance(result.approved_at, datetime)

    # One add for the audit log.
    assert db.add.call_count == 1

    # One commit for the document and one for the audit log.
    assert db.commit.call_count == 2

    audit_log = db.add.call_args_list[-1].args[0]

    assert audit_log.action == "DOCUMENT_APPROVED"
    assert audit_log.user_id == 1
    assert audit_log.entity_type == "Document"
    assert audit_log.entity_id == 1
    assert audit_log.metadata_json == {
        "previous_status": "UPLOADED",
        "new_status": "APPROVED",
    }


def test_approved_document_can_be_deactivated() -> None:
    db = Mock()
    document = create_document(DocumentStatus.APPROVED)

    result = change_document_status(
        db=db,
        document=document,
        new_status=DocumentStatus.INACTIVE,
        actor_user_id=1,
    )

    assert result.status == DocumentStatus.INACTIVE
    assert isinstance(result.deactivated_at, datetime)

    audit_log = db.add.call_args_list[-1].args[0]

    assert audit_log.action == "DOCUMENT_DEACTIVATED"
    assert audit_log.metadata_json == {
        "previous_status": "APPROVED",
        "new_status": "INACTIVE",
    }


def test_invalid_document_status_transition_is_rejected() -> None:
    db = Mock()
    document = create_document(DocumentStatus.INACTIVE)

    with pytest.raises(
        ValueError,
        match="Invalid document status transition",
    ):
        change_document_status(
            db=db,
            document=document,
            new_status=DocumentStatus.APPROVED,
            actor_user_id=1,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_same_document_status_is_rejected() -> None:
    with pytest.raises(
        ValueError,
        match="already in the requested status",
    ):
        validate_document_status_transition(
            current_status=DocumentStatus.UPLOADED,
            new_status=DocumentStatus.UPLOADED,
        )