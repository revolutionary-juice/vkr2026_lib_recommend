from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User


def require_admin(
    x_admin_user_id: int | None = Header(default=None, alias="X-Admin-User-Id"),
    db: Session = Depends(get_db),
) -> User:
    if x_admin_user_id is None:
        raise HTTPException(status_code=401, detail="Admin access requires X-Admin-User-Id")

    user = db.query(User).filter(User.id == x_admin_user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Admin user not found")

    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Admin user is blocked")

    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")

    return user
