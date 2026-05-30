"""
Диагностика рекомендаций для user001.
Проверяет: корректность фильтрации, профиль интересов,
вклад контентной и коллаборативной составляющих.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")

from app.core.database import SessionLocal
from app.models.user import User
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.api.recommendations import (
    get_user_interest_profile,
    get_content_based_recommendations,
    get_collaborative_recommendations,
    get_hybrid_recommendations,
    normalize_scores,
)

db = SessionLocal()

# --- Находим user001 ---
user = db.query(User).filter(User.username == "user001").first()
print(f"=== ПОЛЬЗОВАТЕЛЬ: {user.username} (id={user.id}) ===\n")

# --- Что он уже видел ---
interactions = db.query(Interaction).filter(Interaction.user_id == user.id).all()
ratings = db.query(Rating).filter(Rating.user_id == user.id).all()

seen_ids = {i.document_id for i in interactions}
seen_ids.update(r.document_id for r in ratings)

print(f"Взаимодействия ({len(interactions)}):")
for intr in interactions:
    doc = db.query(Document).filter(Document.id == intr.document_id).first()
    print(f"  [{intr.interaction_type:8s} w={intr.weight}] id={doc.id:3d} | {doc.category:15s} | {doc.title[:55]}")

print(f"\nОценки ({len(ratings)}):")
for r in ratings:
    doc = db.query(Document).filter(Document.id == r.document_id).first()
    print(f"  [score={r.score}] id={doc.id:3d} | {doc.category:15s} | {doc.title[:55]}")

# --- Профиль интересов ---
category_weights, seen_document_ids = get_user_interest_profile(db, user.id)
print(f"\nПрофиль интересов (топ-5 категорий):")
sorted_cats = sorted(category_weights.items(), key=lambda x: -x[1])
for cat, w in sorted_cats[:5]:
    print(f"  {cat:20s}: {w:.3f}")

# --- Контентные рекомендации ---
content_recs = get_content_based_recommendations(user.id, db)
print(f"\nКонтентные рекомендации ({len(content_recs)}):")
for r in content_recs:
    print(f"  score={r['score']:.4f} | id={r['id']:3d} | {r.get('category','?'):15s} | {r['title'][:50]}")

# --- Коллаборативные рекомендации ---
collab_recs = get_collaborative_recommendations(user.id, db)
print(f"\nКоллаборативные рекомендации ({len(collab_recs)}):")
if collab_recs:
    for r in collab_recs:
        print(f"  score={r['score']:.4f} | id={r['id']:3d} | {r.get('category','?'):15s} | {r['title'][:50]}")
else:
    print("  (пусто)")

# --- Гибридные рекомендации ---
content_scores = normalize_scores(content_recs)
collab_scores  = normalize_scores(collab_recs)
print(f"\nПосле нормализации:")
print(f"  Контентные  (топ-3): { {k: round(v,3) for k,v in list(content_scores.items())[:3]} }")
print(f"  Коллабор.   (топ-3): { {k: round(v,3) for k,v in list(collab_scores.items())[:3]} }")

hybrid_recs = get_hybrid_recommendations.__wrapped__(user.id, db) \
    if hasattr(get_hybrid_recommendations, '__wrapped__') else None

# Вызываем напрямую через db
from app.api.recommendations import get_category_multiplier
combined = {}
for doc in content_recs:
    doc_id = int(doc["id"])
    combined[doc_id] = {**doc, "score": content_scores.get(doc_id, 0.0) * 0.8}
for doc in collab_recs:
    doc_id = int(doc["id"])
    cat_bonus = get_category_multiplier(doc.get("category"), category_weights)
    collab_part = collab_scores.get(doc_id, 0.0) * 0.2 * cat_bonus
    if doc_id in combined:
        combined[doc_id]["score"] += collab_part
    else:
        combined[doc_id] = {**doc, "score": collab_part}

results = sorted(
    [item for item in combined.values() if item["score"] > 0],
    key=lambda x: -x["score"]
)[:5]

print(f"\nИТОГОВЫЕ гибридные рекомендации (top-5):")
for r in results:
    in_seen = "!!! УЖЕ ВИДЕЛ" if int(r['id']) in seen_ids else "OK"
    print(f"  score={r['score']:.4f} | id={r['id']:3d} | {r.get('category','?'):15s} | {in_seen} | {r['title'][:45]}")

# --- Проверки корректности ---
print("\n=== ПРОВЕРКИ ===")
rec_ids = {int(r['id']) for r in results}
overlap = rec_ids & seen_ids
if overlap:
    print(f"ОШИБКА: рекомендуются уже просмотренные документы! ids={overlap}")
else:
    print("OK: ни один рекомендованный документ не из истории пользователя")

if collab_recs:
    print("OK: коллаборативная составляющая работает (есть похожие пользователи)")
else:
    print("INFO: коллаборативная составляющая пустая (нет похожих пользователей с пересечением)")

collab_contributing = rec_ids & set(collab_scores.keys())
if collab_contributing:
    print(f"OK: {len(collab_contributing)} из {len(results)} рекомендаций усилены коллаборативно: ids={collab_contributing}")
else:
    print("INFO: коллаборативная часть не добавила новых документов в топ-5")

db.close()
