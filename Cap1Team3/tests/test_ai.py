def test_ai_query_requires_auth(client):
    response = client.post(
        "/api/v1/ai/query",
        json={
            "question": "What is the standard claim workflow?",
            "top_k": 3,
        },
    )

    assert response.status_code in [401, 403]


def test_admin_can_view_ai_logs(client, admin_headers):
    response = client.get("/api/v1/ai/logs", headers=admin_headers)

    assert response.status_code == 200
    assert isinstance(response.json(), list)