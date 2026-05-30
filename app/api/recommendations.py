from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.core.database import get_db
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.search_history import SearchHistory
from app.models.user import User

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


def build_document_text(document: Document) -> str:
    title = ((document.title or "") + " ") * 3
    authors = (document.authors or "") + " "
    abstract = (document.abstract or "") + " "
    keywords = ((document.keywords or "") + " ") * 4
    category = ((document.category or "") + " ") * 5
    rubrics = ((document.rubrics or "") + " ") * 4
    publisher = (document.publisher or "") + " "
    isbn = (document.isbn or "") + " "
    return f"{title}{authors}{abstract}{keywords}{category}{rubrics}{publisher}{isbn}".strip()


def build_similarity_text(document: Document) -> str:
    title = (document.title or "") + " "
    keywords = (document.keywords or "") + " "
    category = (document.category or "") + " "
    abstract = (document.abstract or "") + " "
    rubrics = (document.rubrics or "") + " "

    weighted_title = (title.strip() + " ") * 3
    weighted_keywords = (keywords.strip() + " ") * 4
    weighted_category = (category.strip() + " ") * 3
    weighted_rubrics = (rubrics.strip() + " ") * 3
    weighted_abstract = abstract.strip()

    return f"{weighted_title} {weighted_keywords} {weighted_category} {weighted_rubrics} {weighted_abstract}"


def normalize_scores(items: list[dict]) -> dict[int, float]:
    if not items:
        return {}

    scores = [float(item["score"]) for item in items]
    min_score = min(scores)
    max_score = max(scores)

    if max_score == min_score:
        return {int(item["id"]): 1.0 for item in items}

    return {
        int(item["id"]): (float(item["score"]) - min_score) / (max_score - min_score)
        for item in items
    }


def get_recent_search_queries(db: Session, user_id: int, limit: int = 10) -> list[str]:
    rows = (
        db.query(SearchHistory.query)
        .filter(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.id.desc())
        .limit(limit)
        .all()
    )

    queries: list[str] = []
    seen: set[str] = set()
    for row in rows:
        query = (row[0] or "").strip()
        normalized = query.lower()
        if not query or normalized in seen:
            continue
        seen.add(normalized)
        queries.append(query)

    return queries


def get_user_interest_profile(db: Session, user_id: int) -> tuple[dict[str, float], set[int]]:
    interactions = db.query(Interaction).filter(Interaction.user_id == user_id).all()
    ratings = db.query(Rating).filter(Rating.user_id == user_id).all()

    seen_document_ids = {interaction.document_id for interaction in interactions}
    seen_document_ids.update(rating.document_id for rating in ratings)

    category_weights: dict[str, float] = {}

    document_ids = list(seen_document_ids)
    if document_ids:
        documents = db.query(Document).filter(Document.id.in_(document_ids)).all()
        documents_map = {doc.id: doc for doc in documents}
    else:
        documents_map = {}

    for interaction in interactions:
        document = documents_map.get(interaction.document_id)
        if not document or not document.category:
            continue

        category_weights[document.category] = category_weights.get(document.category, 0.0) + float(interaction.weight)

    for rating in ratings:
        document = documents_map.get(rating.document_id)
        if not document or not document.category:
            continue

        category_weights[document.category] = category_weights.get(document.category, 0.0) + float(rating.score) * 1.5

    return category_weights, seen_document_ids


def get_category_multiplier(category: str | None, category_weights: dict[str, float]) -> float:
    if not category or not category_weights:
        return 1.0

    max_weight = max(category_weights.values())
    current_weight = category_weights.get(category, 0.0)

    if current_weight <= 0:
        return 0.35

    return 1.0 + (current_weight / max_weight) * 0.75


@router.get("/content-based/{user_id}")
def get_content_based_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    category_weights, seen_document_ids = get_user_interest_profile(db, user_id)
    search_queries = get_recent_search_queries(db, user_id)

    if not seen_document_ids and not search_queries:
        return []

    all_documents = db.query(Document).all()
    if not all_documents:
        return []

    interacted_documents = [doc for doc in all_documents if doc.id in seen_document_ids]
    candidate_documents = [doc for doc in all_documents if doc.id not in seen_document_ids]

    if not candidate_documents:
        return []

    all_texts = [build_document_text(doc) for doc in all_documents]
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(all_texts)
    doc_id_to_index = {doc.id: idx for idx, doc in enumerate(all_documents)}

    query_similarity_by_document: dict[int, float] = {}
    if search_queries:
        query_matrix = vectorizer.transform(search_queries)
        query_weights = [max(0.45, 1.0 - idx * 0.1) for idx in range(len(search_queries))]
        total_query_weight = sum(query_weights)

        for candidate in candidate_documents:
            candidate_idx = doc_id_to_index[candidate.id]
            query_similarities = cosine_similarity(tfidf_matrix[candidate_idx], query_matrix)[0]
            weighted_query_similarity = sum(
                similarity * weight for similarity, weight in zip(query_similarities, query_weights, strict=False)
            )
            query_similarity_by_document[candidate.id] = (
                weighted_query_similarity / total_query_weight if total_query_weight else 0.0
            )

    scores = []
    for candidate in candidate_documents:
        candidate_idx = doc_id_to_index[candidate.id]

        document_score = 0.0

        weighted_similarity_sum = 0.0
        total_weight = 0.0

        for interacted in interacted_documents:
            interacted_idx = doc_id_to_index[interacted.id]
            similarity = cosine_similarity(
                tfidf_matrix[candidate_idx],
                tfidf_matrix[interacted_idx]
            )[0][0]

            interaction_weight = 1.0
            if interacted.category:
                interaction_weight = get_category_multiplier(interacted.category, category_weights)

            weighted_similarity_sum += similarity * interaction_weight
            total_weight += interaction_weight

        if total_weight == 0:
            if candidate.id not in query_similarity_by_document:
                continue
        else:
            document_score = weighted_similarity_sum / total_weight
            document_score *= get_category_multiplier(candidate.category, category_weights)

        query_score = query_similarity_by_document.get(candidate.id, 0.0)

        if document_score > 0 and query_score > 0:
            final_score = document_score * 0.85 + query_score * 0.15
        elif document_score > 0:
            final_score = document_score
        else:
            final_score = query_score

        if final_score <= 0:
            continue

        scores.append((candidate, final_score))

    scores.sort(key=lambda item: item[1], reverse=True)

    result = []
    for doc, score in scores[:10]:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "abstract": doc.abstract,
            "keywords": doc.keywords,
            "category": doc.category,
            "score": round(float(score), 4)
        })

    return result[:5]


@router.get("/collaborative/{user_id}")
def get_collaborative_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    category_weights, seen_document_ids = get_user_interest_profile(db, user_id)
    all_interactions = db.query(Interaction).all()
    if not all_interactions or not seen_document_ids:
        return []

    user_items: dict[int, dict[int, int]] = {}
    for interaction in all_interactions:
        user_items.setdefault(interaction.user_id, {})
        user_items[interaction.user_id][interaction.document_id] = (
            user_items[interaction.user_id].get(interaction.document_id, 0) + interaction.weight
        )

    if user_id not in user_items:
        return []

    target_items = user_items[user_id]
    documents_map = {doc.id: doc for doc in db.query(Document).all()}
    scores: dict[int, float] = {}

    for other_user_id, other_items in user_items.items():
        if other_user_id == user_id:
            continue

        common_items = set(target_items.keys()) & set(other_items.keys())
        if not common_items:
            continue

        similarity = 0.0
        for item_id in common_items:
            similarity += min(target_items[item_id], other_items[item_id])

        if similarity <= 0:
            continue

        for item_id, weight in other_items.items():
            if item_id in seen_document_ids:
                continue

            document = documents_map.get(item_id)
            if not document:
                continue

            category_multiplier = get_category_multiplier(document.category, category_weights)
            if category_multiplier <= 0.5:
                continue

            scores[item_id] = scores.get(item_id, 0.0) + similarity * weight * category_multiplier

    filtered_scores = {doc_id: score for doc_id, score in scores.items() if score > 0}
    if not filtered_scores:
        return []

    sorted_scores = sorted(filtered_scores.items(), key=lambda item: item[1], reverse=True)[:10]

    result = []
    for doc_id, score in sorted_scores:
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
            "score": round(float(score), 4)
        })

    return result[:5]


@router.get("/hybrid/{user_id}")
def get_hybrid_recommendations(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    category_weights, seen_document_ids = get_user_interest_profile(db, user_id)
    content_recs = get_content_based_recommendations(user_id, db)
    if not seen_document_ids:
        return content_recs[:5]

    collaborative_recs = get_collaborative_recommendations(user_id, db)

    content_scores = normalize_scores(content_recs)
    collaborative_scores = normalize_scores(collaborative_recs)

    combined: dict[int, dict] = {}

    for doc in content_recs:
        doc_id = int(doc["id"])
        combined[doc_id] = {
            **doc,
            "score": content_scores.get(doc_id, 0.0) * 0.8
        }

    for doc in collaborative_recs:
        doc_id = int(doc["id"])
        category_bonus = get_category_multiplier(doc.get("category"), category_weights)
        collaborative_component = collaborative_scores.get(doc_id, 0.0) * 0.2 * category_bonus

        if doc_id in combined:
            combined[doc_id]["score"] += collaborative_component
        else:
            combined[doc_id] = {
                **doc,
                "score": collaborative_component
            }

    results = []
    for item in combined.values():
        if item["score"] <= 0:
            continue
        item["score"] = round(float(item["score"]), 4)
        results.append(item)

    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:5]


@router.get("/similar/{document_id}")
def get_similar_documents(document_id: int, db: Session = Depends(get_db)):
    target_document = db.query(Document).filter(Document.id == document_id).first()
    if not target_document:
        raise HTTPException(status_code=404, detail="Document not found")

    candidate_documents = (
        db.query(Document)
        .filter(Document.category == target_document.category)
        .all()
    )

    candidate_documents = [doc for doc in candidate_documents if doc.id != target_document.id]
    if not candidate_documents:
        return []

    documents_for_compare = [target_document] + candidate_documents
    texts = [build_similarity_text(doc) for doc in documents_for_compare]
    vectorizer = TfidfVectorizer(stop_words=None)
    tfidf_matrix = vectorizer.fit_transform(texts)

    scores = []
    for idx, doc in enumerate(documents_for_compare[1:], start=1):
        similarity = cosine_similarity(tfidf_matrix[0], tfidf_matrix[idx])[0][0]
        scores.append((doc, similarity))

    scores.sort(key=lambda item: item[1], reverse=True)

    result = []
    for doc, score in scores[:5]:
        result.append({
            "id": doc.id,
            "title": doc.title,
            "authors": doc.authors,
            "year": doc.year,
            "abstract": doc.abstract,
            "keywords": doc.keywords,
            "category": doc.category,
            "score": round(float(score), 4)
        })

    return result
