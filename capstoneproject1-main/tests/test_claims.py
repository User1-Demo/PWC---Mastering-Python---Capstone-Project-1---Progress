def test_create_claim_success(client, admin_headers):
    policy_response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "POL-CLM-1001",
            "policy_type": "MOTOR",
            "holder_name": "Claim Holder",
            "region": "North",
            "coverage_start": "2024-01-01",
            "coverage_end": "2025-12-31",
            "status": "ACTIVE",
        },
    )
    policy_id = policy_response.json()["id"]

    response = client.post(
        "/api/v1/claims",
        headers=admin_headers,
        json={
            "claim_number": "CLM-TEST-1001",
            "policy_id": policy_id,
            "claimant_name": "Claim Holder",
            "claim_type": "MOTOR",
            "region": "North",
            "amount": 10000.00,
            "description": "Vehicle damaged in highway accident",
            "incident_date": "2024-06-15",
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "SUBMITTED"


def test_invalid_claim_transition_rejected(client, admin_headers):
    policy_response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "POL-CLM-2001",
            "policy_type": "MOTOR",
            "holder_name": "Transition Holder",
            "region": "North",
            "coverage_start": "2024-01-01",
            "coverage_end": "2025-12-31",
            "status": "ACTIVE",
        },
    )
    policy_id = policy_response.json()["id"]

    claim_response = client.post(
        "/api/v1/claims",
        headers=admin_headers,
        json={
            "claim_number": "CLM-TEST-2001",
            "policy_id": policy_id,
            "claimant_name": "Transition Holder",
            "claim_type": "MOTOR",
            "region": "North",
            "amount": 8000.00,
            "description": "Damage test claim for invalid transition",
            "incident_date": "2024-07-01",
        },
    )
    claim_id = claim_response.json()["id"]

    response = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=admin_headers,
        json={"status": "APPROVED"},
    )

    assert response.status_code == 400


def test_valid_claim_transition(client, admin_headers):
    policy_response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "POL-CLM-3001",
            "policy_type": "MOTOR",
            "holder_name": "Review Holder",
            "region": "North",
            "coverage_start": "2024-01-01",
            "coverage_end": "2025-12-31",
            "status": "ACTIVE",
        },
    )
    policy_id = policy_response.json()["id"]

    claim_response = client.post(
        "/api/v1/claims",
        headers=admin_headers,
        json={
            "claim_number": "CLM-TEST-3001",
            "policy_id": policy_id,
            "claimant_name": "Review Holder",
            "claim_type": "MOTOR",
            "region": "North",
            "amount": 9000.00,
            "description": "Damage test claim for review",
            "incident_date": "2024-07-01",
        },
    )
    claim_id = claim_response.json()["id"]

    response = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=admin_headers,
        json={
            "status": "UNDER_REVIEW",
            "note": "Initial review started",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "UNDER_REVIEW"


def test_support_cannot_update_claim_status(client, support_headers, admin_headers):
    policy_response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "POL-CLM-4001",
            "policy_type": "MOTOR",
            "holder_name": "Support Test Holder",
            "region": "North",
            "coverage_start": "2024-01-01",
            "coverage_end": "2025-12-31",
            "status": "ACTIVE",
        },
    )
    policy_id = policy_response.json()["id"]

    claim_response = client.post(
        "/api/v1/claims",
        headers=admin_headers,
        json={
            "claim_number": "CLM-TEST-4001",
            "policy_id": policy_id,
            "claimant_name": "Support Test Holder",
            "claim_type": "MOTOR",
            "region": "North",
            "amount": 7000.00,
            "description": "Support user status update test",
            "incident_date": "2024-07-10",
        },
    )
    claim_id = claim_response.json()["id"]

    response = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=support_headers,
        json={"status": "UNDER_REVIEW"},
    )

    assert response.status_code == 403