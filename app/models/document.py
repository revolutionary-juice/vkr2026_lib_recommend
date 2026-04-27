from sqlalchemy import Column, Integer, String, Text

from app.core.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    authors = Column(String, nullable=False)
    year = Column(Integer, nullable=False)
    abstract = Column(Text, nullable=True)
    keywords = Column(String, nullable=True)
    category = Column(String, nullable=True)
    publisher = Column(String, nullable=True)
    isbn = Column(String, nullable=True)
    udk = Column(String, nullable=True)
    bbk = Column(String, nullable=True)
    rubrics = Column(Text, nullable=True)
    source_url = Column(String, nullable=True, unique=True, index=True)
    source_system = Column(String, nullable=True)
    external_id = Column(String, nullable=True)
    has_fulltext = Column(Integer, nullable=False, default=0)
