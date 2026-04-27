from pydantic import BaseModel


class DocumentBase(BaseModel):
    title: str
    authors: str
    year: int
    abstract: str | None = None
    keywords: str | None = None
    category: str | None = None
    publisher: str | None = None
    isbn: str | None = None
    udk: str | None = None
    bbk: str | None = None
    rubrics: str | None = None
    source_url: str | None = None
    source_system: str | None = None
    external_id: str | None = None
    has_fulltext: int = 0


class DocumentResponse(DocumentBase):
    id: int

    class Config:
        from_attributes = True
