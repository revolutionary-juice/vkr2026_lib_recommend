from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(
        or_(User.email == data.identifier, User.username == data.identifier)
    ).first()

    if not user:
        raise HTTPException(status_code=401, detail="Invalid login or password")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="User is blocked")

    if not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid login or password")

    return user
