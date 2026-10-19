def test_admin_can_access_analytics(client, admin_headers):
    response = client.get("/api/v1/analytics/claims", headers=admin_headers)

    assert response.status_code == 200
    assert "total_claims" in response.json()
    assert "approval_rate" in response.json()


def test_manager_can_access_analytics(client, manager_headers):
    response = client.get("/api/v1/analytics/claims", headers=manager_headers)

    assert response.status_code == 200


def test_support_cannot_access_analytics(client, support_headers):
    response = client.get("/api/v1/analytics/claims", headers=support_headers)

    assert response.status_code == 403