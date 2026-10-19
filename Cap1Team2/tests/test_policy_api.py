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
    policy_number: str = "POL-10001",
) -> PolicyCreate:
    return PolicyCreate(
        policy_number=policy_number,
        policyholder_name="John Smith",
        coverage_type="Vehicle",
        region="North",
        coverage_limit=Decimal("50000.00"),
        deductible=Decimal("500.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=PolicyStatus.ACTIVE,
    )


def test_create_policy_successfully() -> None:
    db = Mock()
    db.scalar.return_value = None

    policy = create_policy(
        db=db,
        policy_data=valid_policy_data(),
    )

    assert policy.policy_number == "POL-10001"
    assert policy.policyholder_name == "John Smith"
    assert db.add.call_count == 2
    assert db.commit.call_count == 2
    assert db.refresh.call_count >= 1

def test_create_policy_rejects_duplicate_number() -> None:
    db = Mock()
    db.scalar.return_value = Policy(
        id=1,
        policy_number="POL-10001",
        policyholder_name="Existing User",
        coverage_type="Vehicle",
        region="North",
        coverage_limit=Decimal("50000.00"),
        deductible=Decimal("500.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=PolicyStatus.ACTIVE,
    )

    with pytest.raises(ValueError, match="already exists"):
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

    with pytest.raises(ValueError, match="end date"):
        create_policy(
            db=db,
            policy_data=invalid_data,
        )

    db.add.assert_not_called()
    db.commit.assert_not_called()

def test_update_policy_successfully() -> None:
    db = Mock()

    policy = Policy(
        id=1,
        policy_number="POL-10001",
        policyholder_name="John Smith",
        coverage_type="Vehicle",
        region="North",
        coverage_limit=Decimal("50000.00"),
        deductible=Decimal("500.00"),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        status=PolicyStatus.ACTIVE,
    )

    update_data = PolicyUpdate(
        region="South",
        deductible=Decimal("750.00"),
    )

    result = update_policy(
        db=db,
        policy=policy,
        policy_data=update_data,
    )

    assert result.region == "South"
    assert result.deductible == Decimal("750.00")
    assert db.commit.call_count == 2
    assert db.refresh.call_count >= 1