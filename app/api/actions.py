from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.user import User

router = APIRouter(prefix="/actions", tags=["actions"])


@router.post("/view")
def add_view(user_id: int, document_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_views = (
        db.query(Interaction)
        .filter(
            Interaction.user_id == user_id,
            Interaction.document_id == document_id,
            Interaction.interaction_type == "view"
        )
        .order_by(Interaction.id.asc())
        .all()
    )

    if existing_views:
        interaction = existing_views[0]
        interaction.weight = sum(view.weight for view in existing_views) + 1

        for duplicate in existing_views[1:]:
            db.delete(duplicate)

        db.commit()
        db.refresh(interaction)
    else:
        interaction = Interaction(
            user_id=user_id,
            document_id=document_id,
            interaction_type="view",
            weight=1
        )
        db.add(interaction)
        db.commit()
        db.refresh(interaction)

    return {
        "message": "View added",
        "interaction_id": interaction.id,
        "user_id": user_id,
        "document_id": document_id
    }


@router.post("/favorite")
def add_favorite(user_id: int, document_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_favorite = (
        db.query(Interaction)
        .filter(
            Interaction.user_id == user_id,
            Interaction.document_id == document_id,
            Interaction.interaction_type == "favorite"
        )
        .first()
    )

    if existing_favorite:
        return {
            "message": "Already in favorites",
            "interaction_id": existing_favorite.id,
            "user_id": user_id,
            "document_id": document_id
        }

    interaction = Interaction(
        user_id=user_id,
        document_id=document_id,
        interaction_type="favorite",
        weight=3
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return {
        "message": "Favorite added",
        "interaction_id": interaction.id,
        "user_id": user_id,
        "document_id": document_id
    }


@router.delete("/favorite")
def remove_favorite(user_id: int, document_id: int, db: Session = Depends(get_db)):
    favorite = (
        db.query(Interaction)
        .filter(
            Interaction.user_id == user_id,
            Interaction.document_id == document_id,
            Interaction.interaction_type == "favorite"
        )
        .first()
    )

    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite not found")

    db.delete(favorite)
    db.commit()

    return {
        "message": "Favorite removed",
        "user_id": user_id,
        "document_id": document_id
    }


@router.post("/rate")
def add_or_update_rating(user_id: int, document_id: int, score: int, db: Session = Depends(get_db)):
    if score < 1 or score > 5:
        raise HTTPException(status_code=400, detail="Score must be between 1 and 5")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    existing_rating = (
        db.query(Rating)
        .filter(
            Rating.user_id == user_id,
            Rating.document_id == document_id
        )
        .first()
    )

    if existing_rating:
        existing_rating.score = score
        db.commit()
        db.refresh(existing_rating)
        return {
            "message": "Rating updated",
            "rating_id": existing_rating.id,
            "user_id": user_id,
            "document_id": document_id,
            "score": existing_rating.score
        }

    rating = Rating(
        user_id=user_id,
        document_id=document_id,
        score=score
    )

    db.add(rating)
    db.commit()
    db.refresh(rating)

    return {
        "message": "Rating added",
        "rating_id": rating.id,
        "user_id": user_id,
        "document_id": document_id,
        "score": rating.score
    }
