from datetime import date, timedelta
from pathlib import Path
import uuid

from sqlalchemy import select

from app.models.audit import ChatQueryLog
from app.core.security import decrypt_sensitive_value
from app.models.claim import Claim, ClaimStatusHistory
from app.models.enums import ClaimStatus, DocumentStatus, UserRole
from app.models.user import User


def test_claim_workflow_rag_analytics_and_audit(
    client, db_session, actors, auth_headers, monkeypatch, tmp_path: Path
):
    monkeypatch.setattr(
        "app.api.v1.endpoints.documents.storage_dir",
        tmp_path,
    )
    admin_headers = auth_headers[UserRole.ADMIN]
    adjuster_headers = auth_headers[
        UserRole.CLAIMS_ADJUSTER
    ]
    manager_headers = auth_headers[UserRole.CLAIMS_MANAGER]

    policy_response = client.post(
        "/api/v1/policies",
        headers=admin_headers,
        json={
            "policy_number": "TEST-POL-001",
            "policy_type": "motor",
            "policyholder_name": "Demo Policyholder",
            "coverage_amount": "1000000.00",
            "premium_amount": "20000.00",
            "deductible_amount": "1000.00",
            "region_id": str(actors["region"].id),
            "start_date": (date.today() - timedelta(days=90)).isoformat(),
            "end_date": (date.today() + timedelta(days=90)).isoformat(),
            "status": "active",
        },
    )
    assert policy_response.status_code == 201, policy_response.text
    policy_id = policy_response.json()["id"]

    adjuster = db_session.scalar(
        select(User).where(User.role == UserRole.CLAIMS_ADJUSTER)
    )
    claim_response = client.post(
        "/api/v1/claims",
        headers=adjuster_headers,
        json={
            "policy_id": policy_id,
            "claim_type": "motor",
            "claimant_name": "Sample Claimant",
            "claimant_national_id": "AB1234567",
            "incident_date": date.today().isoformat(),
            "description": "Motor collision damage",
            "claimed_amount": "600000.00",
            "assigned_adjuster_id": str(adjuster.id),
        },
    )
    assert claim_response.status_code == 201, claim_response.text
    claim = claim_response.json()
    claim_id = claim["id"]
    assert claim["status"] == ClaimStatus.SUBMITTED.value
    assignment = client.patch(
        f"/api/v1/claims/{claim_id}/assignment",
        headers=manager_headers,
        json={"adjuster_id": str(adjuster.id)},
    )
    assert assignment.status_code == 200, assignment.text
    claim_record = db_session.get(Claim, uuid.UUID(claim_id))
    assert claim_record is not None
    assert claim_record.claimant_national_id_enc != "AB1234567"
    assert decrypt_sensitive_value(claim_record.claimant_national_id_enc) == "AB1234567"
    assert "claimant_national_id_enc" not in claim

    review = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=adjuster_headers,
        json={"status": "under_review", "note": "Initial review started"},
    )
    assert review.status_code == 200, review.text
    adjuster_approval = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=adjuster_headers,
        json={"status": "approved", "approved_amount": "500000.00"},
    )
    assert adjuster_approval.status_code == 409
    approval = client.patch(
        f"/api/v1/claims/{claim_id}/status",
        headers=manager_headers,
        json={"status": "approved", "approved_amount": "500000.00"},
    )
    assert approval.status_code == 200, approval.text
    history = client.get(
        f"/api/v1/claims/{claim_id}/history",
        headers=adjuster_headers,
    )
    assert history.status_code == 200
    assert [entry["to_status"] for entry in history.json()] == [
        "submitted",
        "under_review",
        "approved",
    ]

    upload = client.post(
        "/api/v1/documents",
        headers=admin_headers,
        data={"doc_type": "guideline", "applies_to": "motor"},
        files={
            "file": (
                "motor_guideline.md",
                "## Collision repair\nMotor collision repair estimates are reviewed against the active policy deductible.",
                "text/markdown",
            )
        },
    )
    assert upload.status_code == 201, upload.text
    document_id = upload.json()["id"]
    query = client.post(
        "/api/v1/ai/query",
        headers=adjuster_headers,
        json={
            "question": "What motor collision repair estimates apply? Contact alex@example.com",
            "policy_type": "motor",
        },
    )
    assert query.status_code == 200, query.text
    assert query.json()["no_match"] is False
    assert query.json()["citations"][0]["document_id"] == document_id
    assert "repair estimates" in query.json()["answer"]
    query_log = db_session.scalar(select(ChatQueryLog))
    assert "alex@example.com" not in query_log.question

    deactivate = client.patch(
        f"/api/v1/documents/{document_id}/status",
        headers=admin_headers,
        json={"status": "inactive"},
    )
    assert deactivate.status_code == 200
    assert deactivate.json()["status"] == DocumentStatus.INACTIVE.value
    no_match = client.post(
        "/api/v1/ai/query",
        headers=adjuster_headers,
        json={"question": "What motor collision repair estimates apply?"},
    )
    assert no_match.status_code == 200
    assert no_match.json()["no_match"] is True
    assert no_match.json()["citations"] == []

    analytics = client.get("/api/v1/analytics/claims", headers=manager_headers)
    assert analytics.status_code == 200, analytics.text
    assert analytics.json()["total_claims"] == 1
    assert analytics.json()["approved_claims"] == 1
    assert analytics.json()["approval_rate"] == 100.0
    assert analytics.json()["by_claim_type"] == [{"label": "motor", "count": 1}]
    support_headers = auth_headers[UserRole.SUPPORT_AGENT]
    denied = client.get("/api/v1/analytics/claims", headers=support_headers)
    assert denied.status_code == 403
    ai_analytics = client.get("/api/v1/analytics/ai", headers=manager_headers)
    assert ai_analytics.status_code == 200
    assert ai_analytics.json()["total_queries"] == 2
    assert ai_analytics.json()["no_match_queries"] == 1

    audit_check = client.get("/api/v1/audit/verify", headers=admin_headers)
    assert audit_check.status_code == 200, audit_check.text
    assert audit_check.json()["is_valid"] is True


def test_list_users_serializes_existing_nonstandard_email_without_mutating(
    client, db_session, actors, auth_headers
):
    user = actors[UserRole.CLAIMS_MANAGER]
    user.email = "manager.(north).001@example.test"
    db_session.commit()

    response = client.get("/api/v1/users", headers=auth_headers[UserRole.ADMIN])

    assert response.status_code == 200, response.text
    listed_user = next(item for item in response.json() if item["id"] == str(user.id))
    assert listed_user["email"] == "manager.(north).001@example.test"
    db_session.refresh(user)
    assert user.email == "manager.(north).001@example.test"


def test_refresh_tokens_are_single_use_and_validation_is_field_specific(
    client, db_session, actors
):
    admin = actors[UserRole.ADMIN]
    login = client.post(
        "/api/v1/auth/login",
        json={"email": admin.email, "password": "SecurePass123"},
    )
    assert login.status_code == 200
    refresh_token = login.json()["refresh_token"]
    refreshed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refreshed.status_code == 200
    replayed = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replayed.status_code == 401

    invalid = client.post(
        "/api/v1/claims",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        json={"claim_type": "unknown"},
    )
    assert invalid.status_code == 422
    assert invalid.json()["errors"]
    assert db_session.scalar(select(ClaimStatusHistory)) is None


def test_deactivating_user_revokes_refresh_and_access_tokens(
    client, actors, auth_headers
):
    admin_headers = auth_headers[UserRole.ADMIN]
    adjuster = actors[UserRole.CLAIMS_ADJUSTER]
    adjuster_login = client.post(
        "/api/v1/auth/login",
        json={"email": adjuster.email, "password": "SecurePass123"},
    )
    assert adjuster_login.status_code == 200

    deactivated = client.patch(
        f"/api/v1/users/{adjuster.id}/active?is_active=false",
        headers=admin_headers,
    )
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False

    refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": adjuster_login.json()["refresh_token"]},
    )
    assert refresh.status_code == 401
    me = client.get(
        "/api/v1/claims",
        headers={"Authorization": f"Bearer {adjuster_login.json()['access_token']}"},
    )
    assert me.status_code == 401
