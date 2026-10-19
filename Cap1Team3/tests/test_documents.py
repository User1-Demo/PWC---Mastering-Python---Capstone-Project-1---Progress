from io import BytesIO


def test_admin_can_upload_document(client, admin_headers):
    file_content = b"Section 1: Claim Workflow. Claims move from submitted to under review and then closed."
    files = {
        "file": ("claims_guidelines.txt", BytesIO(file_content), "text/plain"),
    }
    data = {"title": "Claims Guidelines Test"}

    response = client.post(
        "/api/v1/documents",
        headers=admin_headers,
        files=files,
        data=data,
    )

    assert response.status_code == 201
    assert response.json()["title"] == "Claims Guidelines Test"


def test_manager_cannot_upload_document(client, manager_headers):
    file_content = b"Unauthorized file upload"
    files = {
        "file": ("unauth.txt", BytesIO(file_content), "text/plain"),
    }
    data = {"title": "Unauthorized Doc"}

    response = client.post(
        "/api/v1/documents",
        headers=manager_headers,
        files=files,
        data=data,
    )

    assert response.status_code == 403