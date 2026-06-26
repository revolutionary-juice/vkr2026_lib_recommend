from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    if len(user_data.username) < 3:
        raise HTTPException(status_code=400, detail="Логин должен содержать не менее 3 символов")

    if len(user_data.password) < 8:
        raise HTTPException(status_code=400, detail="Пароль должен содержать не менее 8 символов")

    existing_user = db.query(User).filter(
        (User.username == user_data.username) | (User.email == user_data.email)
    ).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="reader"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.get("/", response_model=list[UserResponse])
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


@router.get("/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/{user_id}/history")
def get_user_history(user_id: int, db: Session = Depends(get_db)):
    interactions = (
        db.query(Interaction, Document)
        .join(Document, Interaction.document_id == Document.id)
        .filter(Interaction.user_id == user_id)
        .order_by(Interaction.id.desc())
        .all()
    )

    grouped_views = {}
    result = []

    for interaction, doc in interactions:
        if interaction.interaction_type == "view":
            key = (doc.id, interaction.interaction_type)

            if key in grouped_views:
                grouped_views[key]["weight"] += interaction.weight
                grouped_views[key]["interaction_id"] = max(
                    grouped_views[key]["interaction_id"],
                    interaction.id
                )
                continue

            grouped_views[key] = {
                "interaction_id": interaction.id,
                "document_id": doc.id,
                "title": doc.title,
                "authors": doc.authors,
                "year": doc.year,
                "category": doc.category,
                "interaction_type": interaction.interaction_type,
                "weight": interaction.weight
            }
            continue

        result.append({
            "interaction_id": interaction.id,
            "document_id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "category": doc.category,
            "interaction_type": interaction.interaction_type,
            "weight": interaction.weight
        })

    result.extend(grouped_views.values())
    result.sort(key=lambda item: item["interaction_id"], reverse=True)
    return result


@router.get("/{user_id}/favorites")
def get_user_favorites(user_id: int, db: Session = Depends(get_db)):
    favorites = (
        db.query(Interaction, Document)
        .join(Document, Interaction.document_id == Document.id)
        .filter(Interaction.user_id == user_id)
        .filter(Interaction.interaction_type == "favorite")
        .order_by(Interaction.id.desc())
        .all()
    )

    result = []
    for interaction, doc in favorites:
        result.append({
            "interaction_id": interaction.id,
            "document_id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "category": doc.category,
            "weight": interaction.weight
        })
    return result


@router.get("/{user_id}/ratings")
def get_user_ratings(user_id: int, db: Session = Depends(get_db)):
    ratings = (
        db.query(Rating, Document)
        .join(Document, Rating.document_id == Document.id)
        .filter(Rating.user_id == user_id)
        .order_by(Rating.id.desc())
        .all()
    )

    result = []
    for rating, doc in ratings:
        result.append({
            "rating_id": rating.id,
            "document_id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "category": doc.category,
            "score": rating.score
        })
    return result
