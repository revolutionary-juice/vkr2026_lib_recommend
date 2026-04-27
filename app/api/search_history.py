from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.search_history import SearchHistory
from app.models.user import User
from app.schemas.search_history import SearchHistoryCreate, SearchHistoryResponse

router = APIRouter(prefix="/search-history", tags=["search-history"])

@router.post("/", response_model=SearchHistoryResponse)
def create_search_history(item: SearchHistoryCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == item.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    record = SearchHistory(user_id=item.user_id, query=item.query)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

@router.get("/user/{user_id}", response_model=list[SearchHistoryResponse])
def get_user_search_history(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    records = db.query(SearchHistory).filter(SearchHistory.user_id == user_id).order_by(SearchHistory.id.desc()).all()
    return records