from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_users_me_requires_authentication():
    response = client.get(
        "/users/me"
    )

    assert response.status_code == 401


def test_claims_require_authentication():
    response = client.get(
        "/claims/"
    )

    assert response.status_code == 401


def test_chats_require_authentication():
    response = client.get(
        "/chats/"
    )

    assert response.status_code == 401