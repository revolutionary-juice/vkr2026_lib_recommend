from pydantic import BaseModel


class SearchHistoryCreate(BaseModel):
    user_id: int
    query: str


class SearchHistoryResponse(BaseModel):
    id: int
    user_id: int
    query: str

    class Config:
        from_attributes = True