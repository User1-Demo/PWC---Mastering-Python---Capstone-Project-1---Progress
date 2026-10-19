from fastapi.testclient import TestClient

from claimiq.main import app

client = TestClient(app)


def test_list_claims_requires_authentication() -> None:
    response = client.get("/api/v1/claims")

    assert response.status_code == 401


def test_create_claim_requires_authentication() -> None:
    response = client.post(
        "/api/v1/claims",
        json={
            "claim_number": "CLM-UNAUTH",
            "policy_id": 1,
            "claim_type": "Vehicle Damage",
            "incident_date": "2025-03-10",
            "claimed_amount": 8500,
            "description": "Test claim",
        },
    )

    assert response.status_code == 401


def test_claim_history_requires_authentication() -> None:
    response = client.get("/api/v1/claims/1/history")

    assert response.status_code == 401