from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument


def test_get_knowledge_document(client):
    db = SessionLocal()

    try:
        document = (
            db.query(KnowledgeDocument)
            .filter(
                KnowledgeDocument.source_name == "Salesforce"
            )
            .first()
        )

        assert document is not None

        document_id = document.id

    finally:
        db.close()

    response = client.get(
        f"/api/v1/knowledge/{document_id}"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["document_id"] == document_id
    assert body["source_name"] == "Salesforce"
    assert body["title"] == "Create Customer in Salesforce"
    assert body["metadata"]["action"] == "create_customer"


def test_missing_knowledge_document_returns_404(client):
    response = client.get(
        "/api/v1/knowledge/"
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404

    body = response.json()

    assert body["detail"] == "Knowledge document not found"


def test_list_knowledge_documents(client):
    response = client.get("/api/v1/knowledge")

    assert response.status_code == 200

    body = response.json()

    assert body["count"] == 3
    assert len(body["documents"]) == 3

    documents = {
        document["source_name"]: document
        for document in body["documents"]
    }

    assert set(documents) == {
        "Salesforce",
        "SAP",
        "Slack",
    }

    assert documents["Salesforce"]["title"] == (
        "Create Customer in Salesforce"
    )
    assert documents["Salesforce"]["metadata"]["action"] == (
        "create_customer"
    )
    assert documents["Salesforce"]["embedded"] is True

    assert documents["SAP"]["metadata"]["action"] == (
        "verify_customer"
    )
    assert documents["SAP"]["embedded"] is True

    assert documents["Slack"]["metadata"]["action"] == (
        "send_notification"
    )
    assert documents["Slack"]["embedded"] is True
