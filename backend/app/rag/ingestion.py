from typing import Any

from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.repositories.knowledge_repository import KnowledgeRepository


class KnowledgeIngestionService:

    def ingest_text(
        self,
        db: Session,
        source_type: str,
        source_name: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        cleaned_content = content.strip()

        if not cleaned_content:
            raise ValueError("Knowledge document content cannot be empty")

        return KnowledgeRepository.create(
            db=db,
            source_type=source_type,
            source_name=source_name,
            title=title.strip(),
            content=cleaned_content,
            metadata=metadata,
        )


knowledge_ingestion_service = KnowledgeIngestionService()