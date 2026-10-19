from fastapi.testclient import TestClient

from claimiq.main import app

client = TestClient(app)


def test_audit_logs_require_authentication() -> None:
    response = client.get("/api/v1/audit-logs")

    assert response.status_code == 401