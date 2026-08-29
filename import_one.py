
import sys

from app.core.database import SessionLocal
from app.models.document import Document
from app.services.dvfu_import import parse_document_card, DvfuImportError


def main() -> None:
    if len(sys.argv) < 2:
        print('Использование: python import_one.py "<URL карточки ДВФУ>"')
        sys.exit(1)

    url = sys.argv[1].strip()
    print("Загружаю карточку:", url)

    db = SessionLocal()
    try:
        try:
            payload = parse_document_card(url)
        except DvfuImportError as exc:
            print("Ошибка обращения к каталогу ДВФУ:", exc)
            sys.exit(2)

        if not payload:
            print("Не удалось распарсить карточку (не найден заголовок). Проверь ссылку.")
            sys.exit(3)

        existing = (
            db.query(Document)
            .filter(Document.source_url == payload["source_url"])
            .first()
        )

        if existing:
            for field, value in payload.items():
                setattr(existing, field, value)
            db.commit()
            db.refresh(existing)
            doc = existing
            print(f"\nДокумент уже был в базе — обновлён. id = {doc.id}")
        else:
            doc = Document(**payload)
            db.add(doc)
            db.commit()
            db.refresh(doc)
            print(f"\nДокумент добавлен. id = {doc.id}")

        print("  Название :", doc.title)
        print("  Авторы   :", doc.authors)
        print("  Год      :", doc.year)
        print("  Категория:", doc.category)
        print("  УДК      :", doc.udk)
    finally:
        db.close()


if __name__ == "__main__":
    main()
