from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.repositories.knowledge_repository import KnowledgeRepository


router = APIRouter(
    prefix="/api/v1/knowledge",
    tags=["Knowledge"],
)

@router.get("")
async def list_knowledge_documents(
    db: Session = Depends(get_db),
):
    documents = KnowledgeRepository.list_all(db)

    return {
        "count": len(documents),
        "documents": [
            {
                "document_id": document.id,
                "source_type": document.source_type,
                "source_name": document.source_name,
                "title": document.title,
                "metadata": document.metadata_json,
                "embedded": document.embedding is not None,
                "created_at": document.created_at,
            }
            for document in documents
        ],
    }

@router.get("/{document_id}")
async def get_knowledge_document(
    document_id: UUID,
    db: Session = Depends(get_db),
):
    document = KnowledgeRepository.get(
        db,
        str(document_id),
    )

    if document is None:
        raise HTTPException(
            status_code=404,
            detail="Knowledge document not found",
        )

    return {
        "document_id": document.id,
        "source_type": document.source_type,
        "source_name": document.source_name,
        "title": document.title,
        "content": document.content,
        "metadata": document.metadata_json,
        "created_at": document.created_at,
    }
