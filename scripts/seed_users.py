"""
Генерация 100 тестовых пользователей с кластеризованными интересами.
Каждый пользователь получает одну основную категорию и 1-2 смежные,
взаимодействует преимущественно с документами своей категории.

Запуск: python seed_users.py
Безопасен для повторного запуска — пропускает уже существующих пользователей.
"""

import random
from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.search_history import SearchHistory
from app.models.user import User

# Воспроизводимость результатов
random.seed(42)

# Поисковые запросы по тематике (используются для search_history)
SEARCH_QUERIES = {
    "Информационные технологии": [
        "алгоритмы", "базы данных", "программирование", "веб-разработка",
        "машинное обучение", "нейронные сети", "кибербезопасность",
    ],
    "Математика": [
        "математический анализ", "линейная алгебра", "теория вероятностей",
        "дискретная математика", "численные методы", "статистика",
    ],
    "Физика": [
        "квантовая механика", "термодинамика", "электродинамика",
        "оптика", "ядерная физика", "механика",
    ],
    "История": [
        "история России", "мировая история", "история науки",
        "древний мир", "средневековье", "новейшая история",
    ],
    "Экономика": [
        "микроэкономика", "макроэкономика", "финансы", "менеджмент",
        "маркетинг", "бухгалтерский учёт", "экономический анализ",
    ],
    "Право": [
        "гражданское право", "конституционное право", "уголовное право",
        "административное право", "международное право",
    ],
    "Биология": [
        "генетика", "молекулярная биология", "экология", "зоология",
        "ботаника", "биохимия", "микробиология",
    ],
    "Химия": [
        "органическая химия", "неорганическая химия", "физическая химия",
        "аналитическая химия", "полимеры",
    ],
    "Философия": [
        "философия науки", "этика", "онтология", "гносеология",
        "логика", "философия техники",
    ],
    "Психология": [
        "когнитивная психология", "социальная психология", "психоанализ",
        "педагогическая психология", "нейропсихология",
    ],
}

# Запросы по умолчанию для категорий не из словаря
DEFAULT_QUERIES = [
    "учебник", "монография", "научная статья",
    "методическое пособие", "исследование",
]


def get_queries_for_category(category: str) -> list[str]:
    for key, queries in SEARCH_QUERIES.items():
        if key.lower() in (category or "").lower() or (category or "").lower() in key.lower():
            return queries
    return DEFAULT_QUERIES


def seed(db):
    # Получаем все документы и группируем по категориям
    all_docs = db.query(Document).all()
    if not all_docs:
        print("ERROR: Документов в БД нет. Сначала импортируй каталог.")
        return

    docs_by_category: dict[str, list[Document]] = {}
    for doc in all_docs:
        cat = doc.category or "Без категории"
        docs_by_category.setdefault(cat, []).append(doc)

    categories = list(docs_by_category.keys())
    print(f"Найдено {len(all_docs)} документов в {len(categories)} категориях:")
    for cat, docs in sorted(docs_by_category.items(), key=lambda x: -len(x[1])):
        print(f"   {cat}: {len(docs)} документов")
    print()

    created = 0
    skipped = 0

    for i in range(1, 101):
        username = f"user{i:03d}"
        email = f"user{i:03d}@test.ru"

        # Пропускаем если уже существует
        if db.query(User).filter(User.username == username).first():
            skipped += 1
            continue

        # Создаём пользователя
        user = User(
            username=username,
            email=email,
            password_hash=hash_password("testpass123"),
            role="reader",
            is_blocked=0,
        )
        db.add(user)
        db.flush()  # получаем user.id

        # Выбираем основную категорию и 1-2 смежные
        primary_cat = categories[i % len(categories)]
        other_cats = [c for c in categories if c != primary_cat]
        secondary_cats = random.sample(other_cats, min(2, len(other_cats)))

        # Документы для взаимодействий
        primary_docs = docs_by_category[primary_cat]
        secondary_docs = []
        for sc in secondary_cats:
            secondary_docs.extend(docs_by_category[sc])

        # --- ПРОСМОТРЫ ---
        # Основная категория: до 14 просмотров, не больше чем документов в категории
        max_primary = len(primary_docs)
        view_count_primary = random.randint(min(4, max_primary), min(14, max_primary))
        viewed_docs = random.sample(primary_docs, view_count_primary)

        for doc in viewed_docs:
            db.add(Interaction(
                user_id=user.id,
                document_id=doc.id,
                interaction_type="view",
                weight=1,
            ))

        # Смежные категории: 2-5 просмотров
        if secondary_docs:
            view_count_secondary = random.randint(1, min(5, len(secondary_docs)))
            secondary_viewed = random.sample(secondary_docs, view_count_secondary)
            for doc in secondary_viewed:
                db.add(Interaction(
                    user_id=user.id,
                    document_id=doc.id,
                    interaction_type="view",
                    weight=1,
                ))

        # --- ИЗБРАННОЕ ---
        # 1-3 документа из основной категории
        fav_count = random.randint(1, min(3, len(viewed_docs)))
        fav_docs = random.sample(viewed_docs, fav_count)
        for doc in fav_docs:
            db.add(Interaction(
                user_id=user.id,
                document_id=doc.id,
                interaction_type="favorite",
                weight=3,
            ))

        # --- ОЦЕНКИ ---
        # 2-3 оценки из просмотренных, преимущественно 4-5
        rating_docs = random.sample(viewed_docs, min(random.randint(2, 3), len(viewed_docs)))
        for doc in rating_docs:
            score = random.choices([3, 4, 5], weights=[1, 3, 4])[0]
            # Проверяем уникальность (модель имеет UniqueConstraint)
            existing = db.query(Rating).filter(
                Rating.user_id == user.id,
                Rating.document_id == doc.id
            ).first()
            if not existing:
                db.add(Rating(
                    user_id=user.id,
                    document_id=doc.id,
                    score=score,
                ))

        # --- ИСТОРИЯ ПОИСКА ---
        # 2-4 поисковых запроса по теме основной категории
        queries = get_queries_for_category(primary_cat)
        search_count = random.randint(2, min(4, len(queries)))
        for q in random.sample(queries, search_count):
            db.add(SearchHistory(
                user_id=user.id,
                query=q,
            ))

        created += 1

    db.commit()
    print(f"Создано пользователей: {created}")
    if skipped:
        print(f"Пропущено (уже существуют): {skipped}")
    print(f"\nПароль для всех новых пользователей: testpass123")
    print("Логины: user001 ... user100")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed(db)
    finally:
        db.close()
