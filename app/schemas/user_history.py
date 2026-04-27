from pydantic import BaseModel


class UserHistoryItem(BaseModel):
    interaction_id: int
    document_id: int
    title: str
    interaction_type: str
    weight: int

    class Config:
        from_attributes = True