import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.interaction import Interaction


def get_collaborative_recommendations(db: Session, user_id: int, top_k: int = 5, min_score: float = 0.01):
    interactions = db.query(Interaction).all()
    documents = db.query(Document).all()

    if not interactions or not documents:
        return []

    interaction_data = []
    for interaction in interactions:
        interaction_data.append({
            "user_id": interaction.user_id,
            "document_id": interaction.document_id,
            "weight": interaction.weight
        })

    df = pd.DataFrame(interaction_data)

    if df.empty:
        return []

    user_item_matrix = df.pivot_table(
        index="user_id",
        columns="document_id",
        values="weight",
        aggfunc="sum",
        fill_value=0
    )

    if user_id not in user_item_matrix.index:
        return []

    item_user_matrix = user_item_matrix.T
    similarity_matrix = cosine_similarity(item_user_matrix)

    similarity_df = pd.DataFrame(
        similarity_matrix,
        index=item_user_matrix.index,
        columns=item_user_matrix.index
    )

    user_interactions = user_item_matrix.loc[user_id]
    interacted_doc_ids = user_interactions[user_interactions > 0].index.tolist()

    scores = {}

    for doc_id in interacted_doc_ids:
        similar_items = similarity_df[doc_id].sort_values(ascending=False)

        for similar_doc_id, score in similar_items.items():
            if similar_doc_id == doc_id:
                continue

            if similar_doc_id in interacted_doc_ids:
                continue

            if score <= min_score:
                continue

            if similar_doc_id not in scores:
                scores[similar_doc_id] = 0

            scores[similar_doc_id] += float(score)

    if not scores:
        return []

    sorted_recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    documents_map = {doc.id: doc for doc in documents}

    result = []
    for doc_id, score in sorted_recommendations[:top_k]:
        if score <= min_score:
            continue

        doc = documents_map.get(doc_id)
        if not doc:
            continue

        result.append({
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "abstract": doc.abstract,
            "keywords": doc.keywords,
            "category": doc.category,
            "score": round(score, 4)
        })

    return result