from sqlalchemy.orm import Session

from app.recommender.content_based import get_content_based_recommendations
from app.recommender.collaborative import get_collaborative_recommendations


def get_hybrid_recommendations(
    db: Session,
    user_id: int,
    top_k: int = 5,
    content_weight: float = 0.6,
    collaborative_weight: float = 0.4
):
    content_recs = get_content_based_recommendations(db, user_id=user_id, top_k=20)
    collaborative_recs = get_collaborative_recommendations(db, user_id=user_id, top_k=20)

    combined_scores = {}

    for rec in content_recs:
        doc_id = rec["id"]
        if doc_id not in combined_scores:
            combined_scores[doc_id] = {
                "document": rec,
                "score": 0
            }
        combined_scores[doc_id]["score"] += rec["score"] * content_weight

    for rec in collaborative_recs:
        doc_id = rec["id"]
        if doc_id not in combined_scores:
            combined_scores[doc_id] = {
                "document": rec,
                "score": 0
            }
        combined_scores[doc_id]["score"] += rec["score"] * collaborative_weight

    if not combined_scores:
        return []

    sorted_recommendations = sorted(
        combined_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    result = []
    for item in sorted_recommendations[:top_k]:
        doc = item["document"].copy()
        doc["score"] = round(item["score"], 4)
        result.append(doc)

    return result