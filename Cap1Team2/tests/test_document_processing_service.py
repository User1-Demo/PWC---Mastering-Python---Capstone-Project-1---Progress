from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from claimiq.models.audit_log import AuditLog
from claimiq.models.document import Document, DocumentStatus
from claimiq.models.document_chunk import DocumentChunk
from claimiq.services.document_processing_service import (
    process_document,
)


def create_test_document(
    file_path: str,
    status: DocumentStatus = DocumentStatus.UPLOADED,
) -> Document:
    return Document(
        id=1,
        title="Vehicle Policy Manual",
        file_name="vehicle_policy.txt",
        file_path=file_path,
        document_type="POLICY_MANUAL",
        version="1.0",
        status=status,
        uploaded_by=1,
    )


def test_process_document_successfully(
    tmp_path: Path,
) -> None:
    document_file = tmp_path / "vehicle_policy.txt"
    document_file.write_text(
        "Collision coverage protects the insured vehicle. "
        "The deductible is five hundred dollars.",
        encoding="utf-8",
    )

    document = create_test_document(
        file_path=str(document_file),
    )

    db = Mock()
    db.get.return_value = document

    with patch(
        "claimiq.services.document_processing_service.extract_text",
        return_value=(
            "Collision coverage protects the insured vehicle. "
            "The deductible is five hundred dollars."
        ),
    ), patch(
        "claimiq.services.document_processing_service.chunk_text",
        return_value=[
            "Collision coverage protects the insured vehicle.",
            "The deductible is five hundred dollars.",
        ],
    ):
        result = process_document(
            db=db,
            document_id=1,
            actor_user_id=2,
            chunk_size=100,
            overlap=20,
        )

    assert result is document
    assert document.status == DocumentStatus.APPROVED

    db.execute.assert_called_once()

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    chunks = [
        item
        for item in added_objects
        if isinstance(item, DocumentChunk)
    ]

    audit_logs = [
        item
        for item in added_objects
        if isinstance(item, AuditLog)
    ]

    assert len(chunks) == 2
    assert chunks[0].document_id == 1
    assert chunks[0].chunk_index == 0
    assert chunks[0].content == (
        "Collision coverage protects the insured vehicle."
    )

    assert chunks[1].document_id == 1
    assert chunks[1].chunk_index == 1
    assert chunks[1].content == (
        "The deductible is five hundred dollars."
    )

    assert len(audit_logs) == 1

    audit_log = audit_logs[0]

    assert audit_log.action == "DOCUMENT_PROCESSED"
    assert audit_log.user_id == 2
    assert audit_log.entity_type == "Document"
    assert audit_log.entity_id == 1
    assert audit_log.metadata_json == {
        "chunk_count": 2,
        "status": "APPROVED",
    }

    # Commit sequence:
    # 1. Set document to PROCESSING
    # 2. Save chunks and set document to APPROVED
    # 3. Save audit log
    assert db.commit.call_count == 3


def test_process_document_deletes_existing_chunks(
    tmp_path: Path,
) -> None:
    document_file = tmp_path / "policy.txt"
    document_file.write_text(
        "Updated policy content.",
        encoding="utf-8",
    )

    document = create_test_document(
        file_path=str(document_file),
    )

    db = Mock()
    db.get.return_value = document

    with patch(
        "claimiq.services.document_processing_service.extract_text",
        return_value="Updated policy content.",
    ), patch(
        "claimiq.services.document_processing_service.chunk_text",
        return_value=["Updated policy content."],
    ):
        process_document(
            db=db,
            document_id=1,
            actor_user_id=2,
        )

    db.execute.assert_called_once()

    delete_statement = db.execute.call_args.args[0]

    assert "document_chunks" in str(delete_statement)
    assert document.status == DocumentStatus.APPROVED


def test_process_document_rejects_missing_document() -> None:
    db = Mock()
    db.get.return_value = None

    with pytest.raises(
        ValueError,
        match="Document not found",
    ):
        process_document(
            db=db,
            document_id=999,
            actor_user_id=2,
        )

    db.execute.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_process_document_rejects_invalid_status(
    tmp_path: Path,
) -> None:
    document_file = tmp_path / "approved_policy.txt"
    document_file.write_text(
        "Already approved content.",
        encoding="utf-8",
    )

    document = create_test_document(
        file_path=str(document_file),
        status=DocumentStatus.APPROVED,
    )

    db = Mock()
    db.get.return_value = document

    with pytest.raises(
        ValueError,
        match="Only uploaded or failed documents can be processed",
    ):
        process_document(
            db=db,
            document_id=1,
            actor_user_id=2,
        )

    db.execute.assert_not_called()
    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_process_document_failure_sets_failed_status(
    tmp_path: Path,
) -> None:
    missing_file = tmp_path / "missing_policy.txt"

    document = create_test_document(
        file_path=str(missing_file),
    )

    db = Mock()

    # First get() loads the document.
    # Second get() reloads it after rollback.
    db.get.side_effect = [document, document]

    with pytest.raises(
        ValueError,
        match="Document processing failed",
    ):
        process_document(
            db=db,
            document_id=1,
            actor_user_id=2,
        )

    assert document.status == DocumentStatus.FAILED
    db.rollback.assert_called_once()

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    audit_logs = [
        item
        for item in added_objects
        if isinstance(item, AuditLog)
    ]

    assert len(audit_logs) == 1

    audit_log = audit_logs[0]

    assert audit_log.action == "DOCUMENT_PROCESSING_FAILED"
    assert audit_log.user_id == 2
    assert audit_log.entity_type == "Document"
    assert audit_log.entity_id == 1
    assert audit_log.metadata_json["status"] == "FAILED"
    assert "error" in audit_log.metadata_json