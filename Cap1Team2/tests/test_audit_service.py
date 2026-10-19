from unittest.mock import Mock

from claimiq.services.audit_service import create_audit_log


def test_create_audit_log_successfully() -> None:
    db = Mock()

    audit_log = create_audit_log(
        db=db,
        action="CLAIM_CREATED",
        user_id=1,
        entity_type="Claim",
        entity_id=10,
        request_id="request-123",
        metadata={
            "claim_number": "CLM-10001",
        },
    )

    assert audit_log.action == "CLAIM_CREATED"
    assert audit_log.user_id == 1
    assert audit_log.entity_type == "Claim"
    assert audit_log.entity_id == 10
    assert audit_log.request_id == "request-123"
    assert audit_log.metadata_json == {
        "claim_number": "CLM-10001",
    }

    db.add.assert_called_once_with(audit_log)
    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(audit_log)


def test_create_audit_log_without_optional_fields() -> None:
    db = Mock()

    audit_log = create_audit_log(
        db=db,
        action="LOGIN_SUCCESS",
    )

    assert audit_log.action == "LOGIN_SUCCESS"
    assert audit_log.user_id is None
    assert audit_log.entity_type is None
    assert audit_log.entity_id is None
    assert audit_log.metadata_json is None