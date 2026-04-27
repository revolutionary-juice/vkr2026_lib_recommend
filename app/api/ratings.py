from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.rating import Rating
from app.models.user import User
from app.schemas.rating import RatingCreate, RatingResponse

router = APIRouter(prefix="/ratings", tags=["ratings"])


@router.post("/", response_model=RatingResponse)
def create_or_update_rating(rating_data: RatingCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == rating_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(Document).filter(Document.id == rating_data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_rating = (
        db.query(Rating)
        .filter(Rating.user_id == rating_data.user_id, Rating.document_id == rating_data.document_id)
        .first()
    )

    if existing_rating:
        existing_rating.score = rating_data.score
        db.commit()
        db.refresh(existing_rating)
        return existing_rating

    rating = Rating(
        user_id=rating_data.user_id,
        document_id=rating_data.document_id,
        score=rating_data.score
    )

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return rating


@router.get("/", response_model=list[RatingResponse])
def get_ratings(db: Session = Depends(get_db)):
    return db.query(Rating).all()


@router.get("/user/{user_id}")
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    ratings = (
        db.query(Rating, Document)
        .join(Document, Rating.document_id == Document.id)
        .filter(Rating.user_id == user_id)
        .all()
    )

    result = []
    for rating, document in ratings:
        result.append({
            "rating_id": rating.id,
            "document_id": document.id,
            "title": document.title,
            "score": rating.score
        })

    return result