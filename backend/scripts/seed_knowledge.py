from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.rag.ingestion import knowledge_ingestion_service

DOCUMENTS = [
    {
        "source_type": "api_documentation",
        "source_name": "Salesforce",
        "title": "Create Customer in Salesforce",
        "content": """
Creates a new customer account in Salesforce.

Tool:
salesforce.create_customer

Use this capability when a business request requires creating
a new customer, account, or onboarding record in Salesforce.

Operation type:
WRITE

Typical inputs:
- customer_name
- email
- phone
- company
- billing_address

The operation creates a customer record and returns a Salesforce
customer identifier.

Because this operation modifies enterprise data, human approval
should be required before execution.
        """,
        "metadata": {
            "system": "Salesforce",
            "action": "create_customer",
            "tool_name": "salesforce.create_customer",
            "action_type": "WRITE",
            "requires_approval": True,
        },
    },
    {
        "source_type": "api_documentation",
        "source_name": "SAP",
        "title": "Verify Customer in SAP",
        "content": """
Verifies whether a customer record exists and is valid in SAP.

Tool:
sap.verify_customer

Use this capability when a workflow needs to confirm that a
customer exists in SAP or validate customer master data.

Operation type:
VALIDATE

Typical inputs:
- customer_id
- customer_name

The operation returns verification status and may return an SAP
customer identifier.

This is a validation operation and normally does not require
human approval.
        """,
        "metadata": {
            "system": "SAP",
            "action": "verify_customer",
            "tool_name": "sap.verify_customer",
            "action_type": "VALIDATE",
            "requires_approval": False,
        },
    },
    {
        "source_type": "api_documentation",
        "source_name": "Slack",
        "title": "Send Workflow Notification to Slack",
        "content": """
Sends a notification message to a Slack workspace or channel.

Tool:
slack.send_notification

Use this capability when a workflow needs to notify a team,
announce completion, report an error, or communicate workflow
status.

Operation type:
NOTIFY

Typical inputs:
- channel
- message

The operation returns delivery status.

This notification operation normally does not require human
approval.
        """,
        "metadata": {
            "system": "Slack",
            "action": "send_notification",
            "tool_name": "slack.send_notification",
            "action_type": "NOTIFY",
            "requires_approval": False,
        },
    },
]


def main() -> None:
    db = SessionLocal()

    try:
        for document in DOCUMENTS:
            existing = db.scalar(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.source_name == document["source_name"],
                    KnowledgeDocument.title == document["title"],
                )
            )

            if existing:
                print(
                    f"Skipped existing: {existing.source_name} "
                    f"- {existing.title}"
                )
                continue

            created = knowledge_ingestion_service.ingest_text(
                db=db,
                source_type=document["source_type"],
                source_name=document["source_name"],
                title=document["title"],
                content=document["content"],
                metadata=document["metadata"],
            )

            print(
                f"Created: {created.source_name} "
                f"- {created.title} "
                f"({created.id})"
            )

    finally:
        db.close()


if __name__ == "__main__":
    main()