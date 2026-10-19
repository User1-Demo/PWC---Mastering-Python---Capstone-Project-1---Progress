from fastapi.testclient import TestClient

from claimiq.main import app

client = TestClient(app)


def test_create_claim_note_requires_authentication() -> None:
    response = client.post(
        "/api/v1/claims/1/notes",
        json={
            "note_text": "Test claim note",
        },
    )

    assert response.status_code == 401


def test_list_claim_notes_requires_authentication() -> None:
    response = client.get("/api/v1/claims/1/notes")

    assert response.status_code == 401