from datetime import date
from decimal import Decimal
from unittest.mock import Mock

import pytest

from claimiq.models.policy import Policy, PolicyStatus
from claimiq.schemas.policy import PolicyCreate, PolicyUpdate
from claimiq.services.policy_service import (
    create_policy,
    update_policy,
)


def valid_policy_data(
    policy_number: str = "POL-AUDIT-TEST",
) -> PolicyCreate:
    return PolicyCreate(
        policy_number=policy_number,
        policyholder_name="Test User",
        coverage_type="Vehicle",
        region="North",
        coverage_limit=Decimal("50000.00"),
        deductible=Decimal("500.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=PolicyStatus.ACTIVE,
    )


def existing_policy() -> Policy:
    return Policy(
        id=1,
        policy_number="POL-AUDIT-TEST",
        policyholder_name="Test User",
        coverage_type="Vehicle",
        region="North",
        coverage_limit=Decimal("50000.00"),
        deductible=Decimal("500.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=PolicyStatus.ACTIVE,
    )


def test_create_policy_creates_audit_log() -> None:
    db = Mock()
    db.scalar.return_value = None

    policy = create_policy(
        db=db,
        policy_data=valid_policy_data(),
        actor_user_id=1,
    )

    assert policy.policy_number == "POL-AUDIT-TEST"

    # First add: Policy
    # Second add: AuditLog
    assert db.add.call_count == 2
    assert db.commit.call_count == 2

    audit_log = db.add.call_args_list[-1].args[0]

    assert audit_log.action == "POLICY_CREATED"
    assert audit_log.user_id == 1
    assert audit_log.entity_type == "Policy"
    assert audit_log.entity_id == policy.id
    assert audit_log.metadata_json is None


def test_update_policy_creates_audit_log() -> None:
    db = Mock()
    policy = existing_policy()

    result = update_policy(
        db=db,
        policy=policy,
        policy_data=PolicyUpdate(
            deductible=Decimal("750.00"),
        ),
        actor_user_id=1,
    )

    assert result.deductible == Decimal("750.00")

    assert db.commit.call_count == 2

    audit_log = db.add.call_args_list[-1].args[0]

    assert audit_log.action == "POLICY_UPDATED"
    assert audit_log.user_id == 1
    assert audit_log.entity_type == "Policy"
    assert audit_log.entity_id == 1
    assert audit_log.metadata_json == {
        "updated_fields": ["deductible"],
    }


def test_create_policy_rejects_duplicate_number() -> None:
    db = Mock()
    db.scalar.return_value = existing_policy()

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        create_policy(
            db=db,
            policy_data=valid_policy_data(),
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_create_policy_rejects_invalid_dates() -> None:
    db = Mock()
    db.scalar.return_value = None

    invalid_data = valid_policy_data(
        policy_number="POL-INVALID-DATE",
    )

    invalid_data.start_date = date(2025, 12, 31)
    invalid_data.end_date = date(2025, 1, 1)

    with pytest.raises(
        ValueError,
        match="end date",
    ):
        create_policy(
            db=db,
            policy_data=invalid_data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()


def test_update_policy_rejects_invalid_dates() -> None:
    db = Mock()
    policy = existing_policy()

    invalid_update = PolicyUpdate(
        start_date=date(2025, 12, 31),
        end_date=date(2025, 1, 1),
    )

    with pytest.raises(
        ValueError,
        match="end date",
    ):
        update_policy(
            db=db,
            policy=policy,
            policy_data=invalid_update,
            actor_user_id=1,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()