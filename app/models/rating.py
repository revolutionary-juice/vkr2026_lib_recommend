from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from app.core.database import Base


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    score = Column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "document_id", name="unique_user_document_rating"),
    )