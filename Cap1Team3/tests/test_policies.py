def test_admin_can_create_policy(client, admin_headers):
    response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "POL-TEST-1001",
            "policy_type": "MOTOR",
            "holder_name": "Policy Holder One",
            "region": "North",
            "coverage_start": "2024-01-01",
            "coverage_end": "2025-01-01",
            "status": "ACTIVE",
        },
    )

    assert response.status_code == 201
    assert response.json()["policy_number"] == "POL-TEST-1001"


def test_duplicate_policy_rejected(client, admin_headers):
    payload = {
        "policy_number": "POL-DUP-1001",
        "policy_type": "MOTOR",
        "holder_name": "Duplicate Policy Holder",
        "region": "North",
        "coverage_start": "2024-01-01",
        "coverage_end": "2025-01-01",
        "status": "ACTIVE",
    }

    assert client.post("/api/v1/policies", headers=admin_headers, json=payload).status_code == 201

    response = client.post("/api/v1/policies", headers=admin_headers, json=payload)

    assert response.status_code == 409


def test_adjuster_can_list_policies(client, adjuster_headers):
    response = client.get("/api/v1/policies", headers=adjuster_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)