from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument


class KnowledgeRepository:

    @staticmethod
    def create(
        db: Session,
        source_type: str,
        source_name: str,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeDocument:
        document = KnowledgeDocument(
            source_type=source_type,
            source_name=source_name,
            title=title,
            content=content,
            metadata_json=metadata,
        )

        db.add(document)
        db.commit()
        db.refresh(document)

        return document

    @staticmethod
    def get(
        db: Session,
        document_id: str,
    ) -> KnowledgeDocument | None:
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id
        )

        return db.scalar(stmt)

    @staticmethod
    def list_all(
        db: Session,
        limit: int = 100,
    ) -> list[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .order_by(KnowledgeDocument.created_at.desc())
            .limit(limit)
        )

        return list(db.scalars(stmt).all())

    @staticmethod
    def find_by_source(
        db: Session,
        source_name: str,
    ) -> list[KnowledgeDocument]:
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.source_name == source_name)
            .order_by(KnowledgeDocument.created_at.desc())
        )

        return list(db.scalars(stmt).all())