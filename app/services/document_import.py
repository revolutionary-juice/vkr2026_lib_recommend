from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from app.models.document import Document


BASE_DIR = Path(__file__).resolve().parents[2]
CSV_PATH = BASE_DIR / "data" / "documents.csv"


def import_documents_from_csv(db: Session) -> int:
    df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    imported_count = 0

    for _, row in df.iterrows():
        document_id = int(row["id"])

        existing_document = db.query(Document).filter(Document.id == document_id).first()
        if existing_document:
            continue

        document = Document(
            id=document_id,
            title=str(row["title"]).strip(),
            authors=str(row["authors"]).strip(),
            year=int(row["year"]),
            abstract=str(row["abstract"]).strip() if pd.notna(row["abstract"]) else None,
            keywords=str(row["keywords"]).strip() if pd.notna(row["keywords"]) else None,
            category=str(row["category"]).strip() if pd.notna(row["category"]) else None,
        )

        db.add(document)
        imported_count += 1

    db.commit()
    return imported_count