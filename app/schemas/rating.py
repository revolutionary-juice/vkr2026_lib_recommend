from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    user_id: int
    document_id: int
    score: int = Field(..., ge=1, le=5)


class RatingResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    score: int

    class Config:
        from_attributes = True