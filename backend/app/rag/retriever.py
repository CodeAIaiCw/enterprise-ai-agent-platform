from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.knowledge_document import KnowledgeDocument
from app.rag.embeddings import embedding_service


@dataclass
class RetrievalResult:
    document: KnowledgeDocument
    cosine_distance: float

    @property
    def similarity(self) -> float:
        return 1.0 - self.cosine_distance


class KnowledgeRetriever:

    def semantic_search(
        self,
        db: Session,
        query: str,
        limit: int = 5,
    ) -> list[RetrievalResult]:
        normalized_query = query.strip()

        if not normalized_query:
            return []

        query_embedding = embedding_service.embed_text(
            normalized_query
        )

        distance = (
            KnowledgeDocument.embedding.cosine_distance(
                query_embedding
            )
        )

        stmt = (
            select(
                KnowledgeDocument,
                distance.label("cosine_distance"),
            )
            .where(
                KnowledgeDocument.embedding.is_not(None)
            )
            .order_by(distance)
            .limit(limit)
        )

        rows = db.execute(stmt).all()

        return [
            RetrievalResult(
                document=row[0],
                cosine_distance=float(row[1]),
            )
            for row in rows
        ]


knowledge_retriever = KnowledgeRetriever()