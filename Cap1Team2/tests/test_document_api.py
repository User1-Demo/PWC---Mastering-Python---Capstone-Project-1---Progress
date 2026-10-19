from fastapi.testclient import TestClient

from claimiq.main import app

client = TestClient(app)


def test_list_documents_requires_authentication() -> None:
    response = client.get("/api/v1/documents")

    assert response.status_code == 401


def test_get_document_requires_authentication() -> None:
    response = client.get("/api/v1/documents/1")

    assert response.status_code == 401


def test_change_document_status_requires_authentication() -> None:
    response = client.patch(
        "/api/v1/documents/1/status",
        json={
            "status": "APPROVED",
        },
    )

    assert response.status_code == 401


def test_upload_document_requires_authentication() -> None:
    response = client.post(
        "/api/v1/documents",
        data={
            "title": "Test Policy",
            "document_type": "POLICY_MANUAL",
            "version": "1.0",
        },
        files={
            "file": (
                "policy.txt",
                b"Test policy content",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 401