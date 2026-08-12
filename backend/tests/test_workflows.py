def create_workflow(client) -> str:
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
    assert len(body["plan"]["steps"]) == 3

    return body["workflow_id"]


def test_workflow_pauses_for_approval(client):
    workflow_id = create_workflow(client)

    response = client.post(
        f"/api/v1/workflows/{workflow_id}/run"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["workflow_id"] == workflow_id
    assert body["status"] == "AWAITING_APPROVAL"

    assert body["interrupt"]["type"] == "approval_required"
    assert body["interrupt"]["workflow_id"] == workflow_id

    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200

    workflow_body = workflow_response.json()

    assert workflow_body["status"] == "AWAITING_APPROVAL"


def test_approved_workflow_completes(client):
    workflow_id = create_workflow(client)

    run_response = client.post(
        f"/api/v1/workflows/{workflow_id}/run"
    )

    assert run_response.status_code == 200
    assert run_response.json()["status"] == "AWAITING_APPROVAL"

    approval_response = client.post(
        f"/api/v1/workflows/{workflow_id}/approve"
    )

    assert approval_response.status_code == 200

    body = approval_response.json()

    assert body["workflow_id"] == workflow_id
    assert body["status"] == "COMPLETED"
    assert body["validation_passed"] is True
    assert body["error"] is None

    results = body["execution_results"]

    assert len(results) == 3

    assert results[0]["system"] == "Salesforce"
    assert results[0]["result"]["status"] == "success"
    assert results[0]["result"]["customer_id"] == "SF-10001"

    assert results[1]["system"] == "SAP"
    assert results[1]["result"]["status"] == "success"
    assert results[1]["result"]["verified"] is True
    assert results[1]["result"]["sap_customer_id"] == "SAP-9001"

    assert results[2]["system"] == "Slack"
    assert results[2]["result"]["status"] == "success"
    assert results[2]["result"]["delivered"] is True

    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "COMPLETED"


def test_approved_workflow_creates_audit_logs(client):
    workflow_id = create_workflow(client)

    run_response = client.post(
        f"/api/v1/workflows/{workflow_id}/run"
    )

    assert run_response.status_code == 200

    approval_response = client.post(
        f"/api/v1/workflows/{workflow_id}/approve"
    )

    assert approval_response.status_code == 200
    assert approval_response.json()["status"] == "COMPLETED"

    logs_response = client.get(
        f"/api/v1/workflows/{workflow_id}/logs"
    )

    assert logs_response.status_code == 200

    body = logs_response.json()

    assert body["workflow_id"] == workflow_id
    assert body["status"] == "COMPLETED"

    logs = body["logs"]

    assert len(logs) == 3

    assert logs[0]["system"] == "Salesforce"
    assert logs[0]["tool_name"] == "salesforce.create_customer"
    assert logs[0]["status"] == "SUCCESS"

    assert logs[1]["system"] == "SAP"
    assert logs[1]["tool_name"] == "sap.verify_customer"
    assert logs[1]["status"] == "SUCCESS"

    assert logs[2]["system"] == "Slack"
    assert logs[2]["tool_name"] == "slack.send_notification"
    assert logs[2]["status"] == "SUCCESS"

    for log in logs:
        assert log["execution_time_ms"] is not None
        assert log["execution_time_ms"] >= 0
        assert log["error"] is None


def test_rejected_workflow_does_not_execute_tools(client):
    workflow_id = create_workflow(client)

    run_response = client.post(
        f"/api/v1/workflows/{workflow_id}/run"
    )

    assert run_response.status_code == 200
    assert run_response.json()["status"] == "AWAITING_APPROVAL"

    rejection_response = client.post(
        f"/api/v1/workflows/{workflow_id}/reject"
    )

    assert rejection_response.status_code == 200

    body = rejection_response.json()

    assert body["workflow_id"] == workflow_id
    assert body["status"] == "REJECTED"

    workflow_response = client.get(
        f"/api/v1/workflows/{workflow_id}"
    )

    assert workflow_response.status_code == 200
    assert workflow_response.json()["status"] == "REJECTED"

    logs_response = client.get(
        f"/api/v1/workflows/{workflow_id}/logs"
    )

    assert logs_response.status_code == 200

    logs = logs_response.json()["logs"]

    assert logs == []


def test_completed_workflow_cannot_be_approved_again(client):
    workflow_id = create_workflow(client)

    client.post(
        f"/api/v1/workflows/{workflow_id}/run"
    )

    first_approval = client.post(
        f"/api/v1/workflows/{workflow_id}/approve"
    )

    assert first_approval.status_code == 200
    assert first_approval.json()["status"] == "COMPLETED"

    second_approval = client.post(
        f"/api/v1/workflows/{workflow_id}/approve"
    )

    assert second_approval.status_code == 409

    assert (
        "not awaiting approval"
        in second_approval.json()["detail"].lower()
    )