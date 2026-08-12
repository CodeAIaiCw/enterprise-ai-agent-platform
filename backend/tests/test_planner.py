def test_grounded_planner_returns_expected_steps(client):
    response = client.post(
        "/api/v1/planner",
        json={
            "request": (
                "Onboard a new client and alert the team "
                "after checking the customer record."
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "PENDING"
    assert "workflow_id" in body

    steps = body["plan"]["steps"]

    assert len(steps) == 3

    assert steps[0]["system"] == "Salesforce"
    assert steps[0]["action"] == "create_customer"
    assert steps[0]["action_type"] == "WRITE"
    assert steps[0]["requires_approval"] is True

    assert steps[1]["system"] == "SAP"
    assert steps[1]["action"] == "verify_customer"
    assert steps[1]["action_type"] == "VALIDATE"

    assert steps[2]["system"] == "Slack"
    assert steps[2]["action"] == "send_notification"
    assert steps[2]["action_type"] == "NOTIFY"


def test_grounded_planner_includes_sources(client):
    response = client.post(
        "/api/v1/planner",
        json={
            "request": (
                "Onboard a new client and alert the team "
                "after checking the customer record."
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    for step in body["plan"]["steps"]:
        assert len(step["sources"]) >= 1

        source = step["sources"][0]

        assert source["document_id"]
        assert source["source_name"]
        assert source["title"]
        assert isinstance(source["similarity"], float)