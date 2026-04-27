from pydantic import BaseModel


class InteractionCreate(BaseModel):
    user_id: int
    document_id: int
    interaction_type: str
    weight: int = 1


class InteractionResponse(BaseModel):
    id: int
    user_id: int
    document_id: int
    interaction_type: str
    weight: int

    class Config:
        from_attributes = True