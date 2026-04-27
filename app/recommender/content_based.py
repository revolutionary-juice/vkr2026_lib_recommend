import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from app.models.document import Document
from app.models.interaction import Interaction


def get_content_based_recommendations(db: Session, user_id: int, top_k: int = 5, min_score: float = 0.15):
    documents = db.query(Document).all()
    interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()

    if not documents or not interactions:
        return []

    docs_data = []
    for doc in documents:
        title_text = ((doc.title or "") + " ") * 3
        keywords_text = ((doc.keywords or "") + " ") * 4
        category_text = ((doc.category or "") + " ") * 2
        abstract_text = (doc.abstract or "")  # слабый вес, без повторения

        combined_text = " ".join([
            title_text.strip(),
            keywords_text.strip(),
            category_text.strip(),
            abstract_text.strip()
        ])

        docs_data.append({
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "abstract": doc.abstract,
            "keywords": doc.keywords,
            "category": doc.category,
            "combined_text": combined_text
        })

    df = pd.DataFrame(docs_data)

    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(df["combined_text"])

    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

    interacted_doc_ids = [interaction.document_id for interaction in interactions]
    interacted_doc_ids = list(set(interacted_doc_ids))

    scores = {}

    for doc_id in interacted_doc_ids:
        doc_index_list = df.index[df["id"] == doc_id].tolist()
        if not doc_index_list:
            continue

        doc_index = doc_index_list[0]
        similar_scores = list(enumerate(similarity_matrix[doc_index]))

        for idx, score in similar_scores:
            recommended_doc_id = int(df.iloc[idx]["id"])

            if recommended_doc_id in interacted_doc_ids:
                continue

            if score < min_score:
                continue

            if recommended_doc_id not in scores:
                scores[recommended_doc_id] = 0

            scores[recommended_doc_id] += float(score)

    sorted_recommendations = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    result = []
    for doc_id, score in sorted_recommendations[:top_k]:
        doc_row = df[df["id"] == doc_id].iloc[0]
        result.append({
            "id": int(doc_row["id"]),
            "title": doc_row["title"],
            "authors": doc_row["authors"],
            "year": int(doc_row["year"]),
            "abstract": doc_row["abstract"],
            "keywords": doc_row["keywords"],
            "category": doc_row["category"],
            "score": round(score, 4)
        })

    return result