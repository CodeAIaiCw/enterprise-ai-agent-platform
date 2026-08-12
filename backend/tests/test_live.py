def test_live_endpoint(client):
    response = client.get("/api/v1/live")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["service"] == "enterprise-ai-agent"
    assert "environment" in body