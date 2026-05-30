from pydantic import BaseModel
from datetime import datetime


class SearchHistoryCreate(BaseModel):
    user_id: int
    query: str


class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    query: str
    created_at: datetime

    class Config:
        from_attributes = True
