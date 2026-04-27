from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.interaction import InteractionCreate, InteractionResponse

router = APIRouter(prefix="/interactions", tags=["interactions"])


@router.post("/", response_model=InteractionResponse)
def create_interaction(interaction_data: InteractionCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == interaction_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    document = db.query(Document).filter(Document.id == interaction_data.document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    interaction = Interaction(
        user_id=interaction_data.user_id,
        document_id=interaction_data.document_id,
        interaction_type=interaction_data.interaction_type,
        weight=interaction_data.weight
    )

    db.add(interaction)
    db.commit()
    db.refresh(interaction)

    return interaction


@router.get("/", response_model=list[InteractionResponse])
def get_interactions(db: Session = Depends(get_db)):
    return db.query(Interaction).all()