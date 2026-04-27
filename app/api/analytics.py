from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.search_history import SearchHistory
from app.models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/system-stats")
def get_system_stats(db: Session = Depends(get_db)):
    documents_count = db.query(func.count(Document.id)).scalar()
    users_count = db.query(func.count(User.id)).scalar()
    interactions_count = db.query(func.count(Interaction.id)).scalar()
    ratings_count = db.query(func.count(Rating.id)).scalar()
    searches_count = db.query(func.count(SearchHistory.id)).scalar()

    return {
        "documents_count": documents_count,
        "users_count": users_count,
        "interactions_count": interactions_count,
        "ratings_count": ratings_count,
        "searches_count": searches_count
    }


@router.get("/popular-categories")
def get_popular_categories(db: Session = Depends(get_db)):
    results = (
        db.query(
            Document.category,
            func.count(Document.id).label("documents_count")
        )
        .group_by(Document.category)
        .order_by(func.count(Document.id).desc())
        .all()
    )

    return [
        {
            "category": row.category,
            "documents_count": row.documents_count
        }
        for row in results
    ]


@router.get("/popular-documents")
def get_analytics_popular_documents(db: Session = Depends(get_db)):
    results = (
        db.query(
            Document.id,
            Document.title,
            func.count(Interaction.id).label("interactions_count")
        )
        .join(Interaction, Interaction.document_id == Document.id)
        .group_by(Document.id, Document.title)
        .having(func.count(Interaction.id) > 0)
        .order_by(func.count(Interaction.id).desc(), Document.id.desc())
        .limit(10)
        .all()
    )

    return [
        {
            "id": row.id,
            "title": row.title,
            "interactions_count": row.interactions_count
        }
        for row in results
    ]