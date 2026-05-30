from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.core.database import get_db
from app.models.document import Document
from app.models.interaction import Interaction
from app.schemas.document import DocumentResponse

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/", response_model=list[DocumentResponse])
def get_documents(
    search: str | None = Query(default=None, description="Поиск по названию, автору, аннотации, ключевым словам"),
    category: str | None = Query(default=None, description="Фильтр по категории"),
    db: Session = Depends(get_db)
):
    query = db.query(Document)

    if search:
        search = search.strip()

    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Document.title.ilike(search_pattern),
                Document.authors.ilike(search_pattern),
                Document.abstract.ilike(search_pattern),
                Document.keywords.ilike(search_pattern),
                Document.rubrics.ilike(search_pattern),
                Document.publisher.ilike(search_pattern),
                Document.isbn.ilike(search_pattern),
                Document.udk.ilike(search_pattern),
                Document.bbk.ilike(search_pattern),
            )
        )

    if category:
        query = query.filter(Document.category.ilike(f"%{category}%"))

    documents = query.all()
    return documents


@router.get("/popular")
def get_popular_documents(limit: int = 10, db: Session = Depends(get_db)):
    results = (
        db.query(
            Document.id,
            Document.title,
            Document.authors,
            Document.year,
            Document.category,
            func.count(Interaction.id).label("interactions_count")
        )
        .join(Interaction, Interaction.document_id == Document.id)
        .group_by(Document.id, Document.title, Document.authors, Document.year, Document.category)
        .having(func.count(Interaction.id) > 0)
        .order_by(func.count(Interaction.id).desc(), Document.id.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "authors": row.authors,
            "year": row.year,
            "category": row.category,
            "interactions_count": row.interactions_count
        }
        for row in results
    ]


@router.get("/recent", response_model=list[DocumentResponse])
def get_recent_documents(limit: int = 10, db: Session = Depends(get_db)):
    documents = (
        db.query(Document)
        .order_by(Document.year.desc(), Document.id.desc())
        .limit(limit)
        .all()
    )

    return documents


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    return document
