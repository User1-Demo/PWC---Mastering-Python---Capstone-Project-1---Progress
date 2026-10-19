from conftest import login


def test_admin_can_create_user(client, admin_headers):
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "New Adjuster",
            "email": "new.adjuster@claimiq.com",
            "password": "Password123",
            "role": "claims_adjuster",
            "region": "West",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "new.adjuster@claimiq.com"
    assert response.json()["role"] == "claims_adjuster"


def test_duplicate_email_rejected(client, admin_headers):
    payload = {
        "full_name": "Duplicate User",
        "email": "duplicate@claimiq.com",
        "password": "Password123",
        "role": "support_agent",
        "region": "West",
    }

    assert client.post("/api/v1/users", headers=admin_headers, json=payload).status_code == 201

    response = client.post("/api/v1/users", headers=admin_headers, json=payload)

    assert response.status_code == 409


def test_short_password_validation(client, admin_headers):
    response = client.post(
        "/api/v1/users",
        headers=admin_headers,
        json={
            "full_name": "Short Password User",
            "email": "shortpw@claimiq.com",
            "password": "123",
            "role": "support_agent",
            "region": "West",
        },
    )

    assert response.status_code == 422


def test_manager_cannot_list_users(client, manager_headers):
    response = client.get("/api/v1/users", headers=manager_headers)

    assert response.status_code == 403


def test_support_cannot_create_user(client, support_headers):
    response = client.post(
        "/api/v1/users",
        headers=support_headers,
        json={
            "full_name": "Blocked User",
            "email": "blocked@claimiq.com",
            "password": "Password123",
            "role": "support_agent",
            "region": "West",
        },
    )

    assert response.status_code == 403


def test_admin_can_deactivate_user(client, admin_headers, seeded_users):
    user_id = seeded_users["support"]["id"]

    response = client.patch(
        f"/api/v1/users/{user_id}/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    login_response = client.post(
        "/api/v1/auth/login",
        json={
            "email": seeded_users["support"]["email"],
            "password": seeded_users["support"]["password"],
        },
    )

    assert login_response.status_code == 401


def test_deactivate_missing_user_returns_404(client, admin_headers):
    response = client.patch(
        "/api/v1/users/999999/status",
        headers=admin_headers,
        json={"is_active": False},
    )

    assert response.status_code == 404