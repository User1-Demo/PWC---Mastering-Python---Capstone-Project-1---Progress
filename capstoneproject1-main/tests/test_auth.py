from conftest import login


def test_login_success(client, seeded_users):
    response = login(
        client,
        seeded_users["admin"]["email"],
        seeded_users["admin"]["password"],
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    assert response.json()["token_type"] == "bearer"


def test_login_wrong_password(client, seeded_users):
    response = login(
        client,
        seeded_users["admin"]["email"],
        "WrongPassword",
    )

    assert response.status_code == 401


def test_refresh_token_success(client, seeded_users):
    login_response = login(
        client,
        seeded_users["admin"]["email"],
        seeded_users["admin"]["password"],
    )

    refresh_token = login_response.json()["refresh_token"]

    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


def test_refresh_token_invalid(client):
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"},
    )

    assert response.status_code == 401