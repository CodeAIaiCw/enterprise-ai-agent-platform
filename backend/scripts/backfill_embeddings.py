from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.knowledge_document import KnowledgeDocument
from app.rag.embeddings import embedding_service


def main() -> None:
    db = SessionLocal()

    try:
        documents = list(
            db.scalars(
                select(KnowledgeDocument).where(
                    KnowledgeDocument.embedding.is_(None)
                )
            ).all()
        )

        if not documents:
            print("No documents require embedding backfill.")
            return

        for document in documents:
            text = (
                f"{document.title}\n\n"
                f"{document.content}"
            )

            document.embedding = embedding_service.embed_text(text)

            print(
                f"Embedded: {document.source_name} "
                f"- {document.title}"
            )

        db.commit()

        print(
            f"Backfill complete. "
            f"Embedded {len(documents)} documents."
        )

    finally:
        db.close()


if __name__ == "__main__":
    main()