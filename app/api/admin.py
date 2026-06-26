import csv
import io
import json
from collections import defaultdict

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.recommendations import (
    get_collaborative_recommendations,
    get_content_based_recommendations,
    get_hybrid_recommendations,
)
from app.core.admin_auth import require_admin
from app.core.database import get_db
from app.core.runtime_logs import get_error_events, get_failed_requests
from app.models.document import Document
from app.models.interaction import Interaction
from app.models.rating import Rating
from app.models.search_history import SearchHistory
from app.models.user import User
from app.services.document_categorization import autocategorize_documents
from app.services.dvfu_import import DvfuImportError, import_dvfu_documents
from app.services.document_import import import_documents_from_csv

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])


class AdminDocumentPayload(BaseModel):
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


class AdminUserUpdatePayload(BaseModel):
    role: str | None = None
    is_blocked: bool | None = None


class MergeDocumentsPayload(BaseModel):
    source_document_id: int
    target_document_id: int


class DvfuImportPayload(BaseModel):
    query: str
    pages: int = 1
    max_records: int = 10


def _serialize_csv(rows: list[dict], filename: str) -> StreamingResponse:
    output = io.StringIO()
    if rows:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    else:
        output.write("")

    response = StreamingResponse(iter([output.getvalue()]), media_type="text/csv; charset=utf-8")
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def _get_user_or_404(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.get("/overview")
def get_admin_overview(db: Session = Depends(get_db)):
    documents_count = db.query(func.count(Document.id)).scalar() or 0
    users_count = db.query(func.count(User.id)).scalar() or 0
    views_count = (
        db.query(func.coalesce(func.sum(Interaction.weight), 0))
        .filter(Interaction.interaction_type == "view")
        .scalar()
        or 0
    )
    favorites_count = (
        db.query(func.count(Interaction.id))
        .filter(Interaction.interaction_type == "favorite")
        .scalar()
        or 0
    )
    ratings_count = db.query(func.count(Rating.id)).scalar() or 0
    searches_count = db.query(func.count(SearchHistory.id)).scalar() or 0

    popular_documents = (
        db.query(
            Document.id,
            Document.title,
            func.count(Interaction.id).label("interactions_count"),
        )
        .join(Interaction, Interaction.document_id == Document.id)
        .group_by(Document.id, Document.title)
        .order_by(func.count(Interaction.id).desc(), Document.id.desc())
        .limit(10)
        .all()
    )

    popular_categories = (
        db.query(
            Document.category,
            func.count(Interaction.id).label("interactions_count"),
        )
        .join(Interaction, Interaction.document_id == Document.id)
        .group_by(Document.category)
        .order_by(func.count(Interaction.id).desc(), Document.category.asc())
        .limit(10)
        .all()
    )

    favorite_documents = (
        db.query(
            Document.id,
            Document.title,
            func.count(Interaction.id).label("favorites_count"),
        )
        .join(Interaction, Interaction.document_id == Document.id)
        .filter(Interaction.interaction_type == "favorite")
        .group_by(Document.id, Document.title)
        .order_by(func.count(Interaction.id).desc(), Document.id.desc())
        .limit(10)
        .all()
    )

    category_view_analytics = (
        db.query(
            func.coalesce(Document.category, "Uncategorized").label("category"),
            func.count(func.distinct(Document.id)).label("documents_count"),
            func.count(func.distinct(Interaction.user_id)).label("unique_viewers"),
            func.coalesce(func.sum(Interaction.weight), 0).label("views_count"),
        )
        .outerjoin(
            Interaction,
            (Interaction.document_id == Document.id) & (Interaction.interaction_type == "view"),
        )
        .group_by(func.coalesce(Document.category, "Uncategorized"))
        .order_by(
            func.count(func.distinct(Interaction.user_id)).desc(),
            func.coalesce(func.sum(Interaction.weight), 0).desc(),
            func.coalesce(Document.category, "Uncategorized").asc(),
        )
        .all()
    )

    return {
        "counts": {
            "documents": documents_count,
            "users": users_count,
            "views": int(views_count),
            "favorites": favorites_count,
            "ratings": ratings_count,
            "searches": searches_count,
        },
        "popular_documents": [
            {"id": row.id, "title": row.title, "interactions_count": row.interactions_count}
            for row in popular_documents
        ],
        "popular_categories": [
            {"category": row.category or "Uncategorized", "interactions_count": row.interactions_count}
            for row in popular_categories
        ],
        "favorite_documents": [
            {"id": row.id, "title": row.title, "favorites_count": row.favorites_count}
            for row in favorite_documents
        ],
        "category_view_analytics": [
            {
                "category": row.category,
                "documents_count": int(row.documents_count or 0),
                "unique_viewers": int(row.unique_viewers or 0),
                "views_count": int(row.views_count or 0),
            }
            for row in category_view_analytics
        ],
    }


@router.get("/catalog/options")
def get_catalog_options(db: Session = Depends(get_db)):
    categories = [
        row[0]
        for row in db.query(Document.category)
        .filter(Document.category.isnot(None))
        .distinct()
        .order_by(Document.category.asc())
        .all()
    ]
    authors = [
        row[0]
        for row in db.query(Document.authors)
        .filter(Document.authors.isnot(None))
        .distinct()
        .order_by(Document.authors.asc())
        .all()
    ]
    years = [row[0] for row in db.query(Document.year).distinct().order_by(Document.year.desc()).all()]
    return {"categories": categories, "authors": authors, "years": years}


@router.get("/documents")
def get_admin_documents(
    search: str | None = None,
    category: str | None = None,
    author: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Document)

    if search:
        pattern = f"%{search}%"
        query = query.filter(
            or_(
                Document.title.ilike(pattern),
                Document.authors.ilike(pattern),
                Document.abstract.ilike(pattern),
                Document.keywords.ilike(pattern),
                Document.rubrics.ilike(pattern),
                Document.publisher.ilike(pattern),
                Document.isbn.ilike(pattern),
            )
        )

    if category:
        query = query.filter(Document.category.ilike(f"%{category}%"))
    if author:
        query = query.filter(Document.authors.ilike(f"%{author}%"))
    if year is not None:
        query = query.filter(Document.year == year)

    documents = query.order_by(Document.id.desc()).all()
    return documents


@router.post("/documents/autocategorize")
def autocategorize_admin_documents(db: Session = Depends(get_db)):
    result = autocategorize_documents(db, overwrite=True)
    return result.__dict__


@router.get("/documents/{document_id}")
def get_admin_document(document_id: int, db: Session = Depends(get_db)):
    return _get_document_or_404(db, document_id)


@router.post("/documents")
def create_admin_document(payload: AdminDocumentPayload, db: Session = Depends(get_db)):
    document = Document(**payload.model_dump())
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


@router.put("/documents/{document_id}")
def update_admin_document(document_id: int, payload: AdminDocumentPayload, db: Session = Depends(get_db)):
    document = _get_document_or_404(db, document_id)
    for field, value in payload.model_dump().items():
        setattr(document, field, value)
    db.commit()
    db.refresh(document)
    return document


@router.delete("/documents/{document_id}")
def delete_admin_document(document_id: int, db: Session = Depends(get_db)):
    document = _get_document_or_404(db, document_id)
    db.query(Interaction).filter(Interaction.document_id == document_id).delete()
    db.query(Rating).filter(Rating.document_id == document_id).delete()
    db.delete(document)
    db.commit()
    return {"message": "Document deleted", "document_id": document_id}


@router.post("/documents/import-csv")
def import_documents_csv(db: Session = Depends(get_db)):
    imported = import_documents_from_csv(db)
    return {"imported": imported}


@router.post("/documents/import-dvfu")
def import_documents_dvfu(payload: DvfuImportPayload, db: Session = Depends(get_db)):
    if payload.pages < 1 or payload.pages > 3:
        raise HTTPException(status_code=400, detail="Pages must be between 1 and 3")
    if payload.max_records < 1 or payload.max_records > 30:
        raise HTTPException(status_code=400, detail="Max records must be between 1 and 30")

    try:
        result = import_dvfu_documents(
            db,
            query=payload.query,
            pages=payload.pages,
            max_records=payload.max_records,
            delay_seconds=3.0,
        )
    except DvfuImportError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return result.__dict__


@router.post("/documents/merge")
def merge_documents(payload: MergeDocumentsPayload, db: Session = Depends(get_db)):
    if payload.source_document_id == payload.target_document_id:
        raise HTTPException(status_code=400, detail="Source and target documents must differ")

    source = _get_document_or_404(db, payload.source_document_id)
    target = _get_document_or_404(db, payload.target_document_id)

    source_ratings = db.query(Rating).filter(Rating.document_id == source.id).all()
    for rating in source_ratings:
        existing_target_rating = (
            db.query(Rating)
            .filter(Rating.user_id == rating.user_id, Rating.document_id == target.id)
            .first()
        )
        if existing_target_rating:
            existing_target_rating.score = max(existing_target_rating.score, rating.score)
            db.delete(rating)
        else:
            rating.document_id = target.id

    source_interactions = db.query(Interaction).filter(Interaction.document_id == source.id).all()
    grouped_interactions: dict[tuple[int, str], Interaction] = {}
    for interaction in (
        db.query(Interaction)
        .filter(Interaction.document_id == target.id)
        .order_by(Interaction.id.asc())
        .all()
    ):
        grouped_interactions[(interaction.user_id, interaction.interaction_type)] = interaction

    for interaction in source_interactions:
        key = (interaction.user_id, interaction.interaction_type)
        existing_interaction = grouped_interactions.get(key)
        if existing_interaction:
            existing_interaction.weight += interaction.weight
            db.delete(interaction)
        else:
            interaction.document_id = target.id
            grouped_interactions[key] = interaction

    db.delete(source)
    db.commit()

    return {
        "message": "Documents merged",
        "source_document_id": payload.source_document_id,
        "target_document_id": payload.target_document_id,
        "target_title": target.title,
    }


@router.get("/users")
def get_admin_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.id.asc()).all()

    # Агрегация одним запросом на каждую метрику вместо N запросов на каждого пользователя
    view_counts = dict(
        db.query(Interaction.user_id, func.coalesce(func.sum(Interaction.weight), 0))
        .filter(Interaction.interaction_type == "view")
        .group_by(Interaction.user_id)
        .all()
    )
    favorite_counts = dict(
        db.query(Interaction.user_id, func.count(Interaction.id))
        .filter(Interaction.interaction_type == "favorite")
        .group_by(Interaction.user_id)
        .all()
    )
    rating_counts = dict(
        db.query(Rating.user_id, func.count(Rating.id))
        .group_by(Rating.user_id)
        .all()
    )
    search_counts = dict(
        db.query(SearchHistory.user_id, func.count(SearchHistory.id))
        .group_by(SearchHistory.user_id)
        .all()
    )

    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_blocked": bool(u.is_blocked),
            "views_count": int(view_counts.get(u.id, 0)),
            "favorites_count": int(favorite_counts.get(u.id, 0)),
            "ratings_count": int(rating_counts.get(u.id, 0)),
            "searches_count": int(search_counts.get(u.id, 0)),
        }
        for u in users
    ]


@router.get("/users/{user_id}")
def get_admin_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    recent_interactions = (
        db.query(Interaction, Document)
        .join(Document, Interaction.document_id == Document.id)
        .filter(Interaction.user_id == user_id)
        .order_by(Interaction.id.desc())
        .limit(15)
        .all()
    )
    recent_searches = (
        db.query(SearchHistory)
        .filter(SearchHistory.user_id == user_id)
        .order_by(SearchHistory.id.desc())
        .limit(15)
        .all()
    )

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "is_blocked": bool(user.is_blocked),
        },
        "recent_interactions": [
            {
                "id": interaction.id,
                "document_id": document.id,
                "document_title": document.title,
                "interaction_type": interaction.interaction_type,
                "weight": interaction.weight,
                "created_at": interaction.created_at,
            }
            for interaction, document in recent_interactions
        ],
        "recent_searches": [
            {"id": row.id, "query": row.query, "created_at": row.created_at}
            for row in recent_searches
        ],
    }


@router.patch("/users/{user_id}")
def update_admin_user(user_id: int, payload: AdminUserUpdatePayload, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    if payload.role is not None:
        user.role = payload.role
    if payload.is_blocked is not None:
        user.is_blocked = 1 if payload.is_blocked else 0
    db.commit()
    db.refresh(user)
    return user


@router.delete("/users/{user_id}")
def delete_admin_user(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Built-in admin cannot be deleted")

    db.query(Interaction).filter(Interaction.user_id == user_id).delete()
    db.query(Rating).filter(Rating.user_id == user_id).delete()
    db.query(SearchHistory).filter(SearchHistory.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    return {"message": "User deleted", "user_id": user_id}


@router.get("/interactions")
def get_admin_interactions(
    user_id: int | None = None,
    document_id: int | None = None,
    interaction_type: str | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Interaction, User.username, Document.title)
        .join(User, User.id == Interaction.user_id)
        .join(Document, Document.id == Interaction.document_id)
    )
    if user_id is not None:
        query = query.filter(Interaction.user_id == user_id)
    if document_id is not None:
        query = query.filter(Interaction.document_id == document_id)
    if interaction_type:
        query = query.filter(Interaction.interaction_type == interaction_type)

    rows = query.order_by(Interaction.id.desc()).limit(300).all()
    return [
        {
            "id": interaction.id,
            "user_id": interaction.user_id,
            "username": username,
            "document_id": interaction.document_id,
            "document_title": title,
            "interaction_type": interaction.interaction_type,
            "weight": interaction.weight,
            "created_at": interaction.created_at,
        }
        for interaction, username, title in rows
    ]


@router.delete("/interactions/{interaction_id}")
def delete_admin_interaction(interaction_id: int, db: Session = Depends(get_db)):
    interaction = db.query(Interaction).filter(Interaction.id == interaction_id).first()
    if not interaction:
        raise HTTPException(status_code=404, detail="Interaction not found")
    db.delete(interaction)
    db.commit()
    return {"message": "Interaction deleted", "interaction_id": interaction_id}


@router.get("/ratings")
def get_admin_ratings(
    user_id: int | None = None,
    document_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = (
        db.query(Rating, User.username, Document.title)
        .join(User, User.id == Rating.user_id)
        .join(Document, Document.id == Rating.document_id)
    )
    if user_id is not None:
        query = query.filter(Rating.user_id == user_id)
    if document_id is not None:
        query = query.filter(Rating.document_id == document_id)

    rows = query.order_by(Rating.id.desc()).limit(300).all()
    return [
        {
            "id": rating.id,
            "user_id": rating.user_id,
            "username": username,
            "document_id": rating.document_id,
            "document_title": title,
            "score": rating.score,
        }
        for rating, username, title in rows
    ]


@router.delete("/ratings/{rating_id}")
def delete_admin_rating(rating_id: int, db: Session = Depends(get_db)):
    rating = db.query(Rating).filter(Rating.id == rating_id).first()
    if not rating:
        raise HTTPException(status_code=404, detail="Rating not found")
    db.delete(rating)
    db.commit()
    return {"message": "Rating deleted", "rating_id": rating_id}


@router.get("/search-history")
def get_admin_search_history(
    user_id: int | None = None,
    query_text: str | None = Query(default=None, alias="query"),
    db: Session = Depends(get_db),
):
    query = db.query(SearchHistory, User.username).join(User, User.id == SearchHistory.user_id)
    if user_id is not None:
        query = query.filter(SearchHistory.user_id == user_id)
    if query_text:
        query = query.filter(SearchHistory.query.ilike(f"%{query_text}%"))

    rows = query.order_by(SearchHistory.id.desc()).limit(300).all()
    return [
        {
            "id": search.id,
            "user_id": search.user_id,
            "username": username,
            "query": search.query,
            "created_at": search.created_at,
        }
        for search, username in rows
    ]


@router.delete("/search-history/{search_id}")
def delete_admin_search_history(search_id: int, db: Session = Depends(get_db)):
    record = db.query(SearchHistory).filter(SearchHistory.id == search_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Search record not found")
    db.delete(record)
    db.commit()
    return {"message": "Search record deleted", "search_id": search_id}


@router.post("/cleanup-duplicates")
def cleanup_duplicate_records(db: Session = Depends(get_db)):
    favorite_groups: dict[tuple[int, int], list[Interaction]] = defaultdict(list)
    view_groups: dict[tuple[int, int], list[Interaction]] = defaultdict(list)
    for interaction in (
        db.query(Interaction)
        .filter(Interaction.interaction_type.in_(["favorite", "view"]))
        .order_by(Interaction.id.desc())
        .all()
    ):
        key = (interaction.user_id, interaction.document_id)
        if interaction.interaction_type == "favorite":
            favorite_groups[key].append(interaction)
        else:
            view_groups[key].append(interaction)

    removed_favorites = 0
    merged_views = 0
    for items in favorite_groups.values():
        for duplicate in items[1:]:
            db.delete(duplicate)
            removed_favorites += 1

    for items in view_groups.values():
        if len(items) <= 1:
            continue
        keeper = items[0]
        keeper.weight = sum(item.weight for item in items)
        for duplicate in items[1:]:
            db.delete(duplicate)
            merged_views += 1

    search_groups: dict[tuple[int, str], list[SearchHistory]] = defaultdict(list)
    for row in db.query(SearchHistory).order_by(SearchHistory.id.desc()).all():
        search_groups[(row.user_id, row.query.strip().lower())].append(row)

    removed_search_duplicates = 0
    for items in search_groups.values():
        for duplicate in items[1:]:
            db.delete(duplicate)
            removed_search_duplicates += 1

    db.commit()
    return {
        "removed_favorite_duplicates": removed_favorites,
        "merged_view_duplicates": merged_views,
        "removed_search_duplicates": removed_search_duplicates,
    }


@router.get("/recommendations/{user_id}")
def get_recommendation_diagnostics(user_id: int, db: Session = Depends(get_db)):
    user = _get_user_or_404(db, user_id)

    source_documents = (
        db.query(Document)
        .filter(
            Document.id.in_(
                list(
                    {
                        row[0]
                        for row in db.query(Interaction.document_id).filter(Interaction.user_id == user_id).all()
                    }
                    | {
                        row[0]
                        for row in db.query(Rating.document_id).filter(Rating.user_id == user_id).all()
                    }
                )
            )
        )
        .order_by(Document.id.asc())
        .all()
    )

    content = get_content_based_recommendations(user_id, db)
    collaborative = get_collaborative_recommendations(user_id, db)
    hybrid = get_hybrid_recommendations(user_id, db)

    return {
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
        },
        "source_documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "authors": doc.authors,
                "year": doc.year,
                "category": doc.category,
            }
            for doc in source_documents
        ],
        "content_based": content,
        "collaborative": collaborative,
        "hybrid": hybrid,
        "is_empty": not (content or collaborative or hybrid),
    }


@router.get("/logs")
def get_admin_logs(db: Session = Depends(get_db)):

    empty_recommendations = []

    duplicate_views = (
        db.query(Interaction.user_id, Interaction.document_id, func.count(Interaction.id).label("duplicates"))
        .filter(Interaction.interaction_type == "view")
        .group_by(Interaction.user_id, Interaction.document_id)
        .having(func.count(Interaction.id) > 1)
        .all()
    )
    duplicate_favorites = (
        db.query(Interaction.user_id, Interaction.document_id, func.count(Interaction.id).label("duplicates"))
        .filter(Interaction.interaction_type == "favorite")
        .group_by(Interaction.user_id, Interaction.document_id)
        .having(func.count(Interaction.id) > 1)
        .all()
    )

    return {
        "failed_requests": get_failed_requests(),
        "error_events": get_error_events(),
        "empty_recommendations": empty_recommendations,
        "duplicate_views": [
            {"user_id": row.user_id, "document_id": row.document_id, "duplicates": row.duplicates}
            for row in duplicate_views
        ],
        "duplicate_favorites": [
            {"user_id": row.user_id, "document_id": row.document_id, "duplicates": row.duplicates}
            for row in duplicate_favorites
        ],
    }


@router.get("/export/{entity}")
def export_entity(entity: str, db: Session = Depends(get_db)):
    if entity == "documents":
        rows = [
            {
                "id": doc.id,
                "title": doc.title,
                "authors": doc.authors,
                "year": doc.year,
                "abstract": doc.abstract or "",
                "keywords": doc.keywords or "",
                "category": doc.category or "",
                "publisher": doc.publisher or "",
                "isbn": doc.isbn or "",
                "udk": doc.udk or "",
                "bbk": doc.bbk or "",
                "rubrics": doc.rubrics or "",
                "source_url": doc.source_url or "",
                "source_system": doc.source_system or "",
                "external_id": doc.external_id or "",
                "has_fulltext": doc.has_fulltext,
            }
            for doc in db.query(Document).order_by(Document.id.asc()).all()
        ]
    elif entity == "users":
        rows = [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_blocked": int(bool(user.is_blocked)),
            }
            for user in db.query(User).order_by(User.id.asc()).all()
        ]
    elif entity == "history":
        rows = [
            {
                "id": row.id,
                "user_id": row.user_id,
                "document_id": row.document_id,
                "interaction_type": row.interaction_type,
                "weight": row.weight,
                "created_at": row.created_at,
            }
            for row in db.query(Interaction).order_by(Interaction.id.asc()).all()
        ]
    else:
        raise HTTPException(status_code=404, detail="Unsupported export entity")

    return _serialize_csv(rows, f"{entity}.csv")


@router.get("/backup")
def backup_database(db: Session = Depends(get_db)):
    payload = {
        "users": [
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "is_blocked": int(bool(user.is_blocked)),
            }
            for user in db.query(User).order_by(User.id.asc()).all()
        ],
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "authors": doc.authors,
                "year": doc.year,
                "abstract": doc.abstract,
                "keywords": doc.keywords,
                "category": doc.category,
                "publisher": doc.publisher,
                "isbn": doc.isbn,
                "udk": doc.udk,
                "bbk": doc.bbk,
                "rubrics": doc.rubrics,
                "source_url": doc.source_url,
                "source_system": doc.source_system,
                "external_id": doc.external_id,
                "has_fulltext": doc.has_fulltext,
            }
            for doc in db.query(Document).order_by(Document.id.asc()).all()
        ],
        "interactions": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "document_id": row.document_id,
                "interaction_type": row.interaction_type,
                "weight": row.weight,
                "created_at": str(row.created_at),
            }
            for row in db.query(Interaction).order_by(Interaction.id.asc()).all()
        ],
        "ratings": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "document_id": row.document_id,
                "score": row.score,
            }
            for row in db.query(Rating).order_by(Rating.id.asc()).all()
        ],
        "search_history": [
            {
                "id": row.id,
                "user_id": row.user_id,
                "query": row.query,
                "created_at": str(row.created_at),
            }
            for row in db.query(SearchHistory).order_by(SearchHistory.id.asc()).all()
        ],
    }

    content = json.dumps(payload, ensure_ascii=False, indent=2)
    response = StreamingResponse(iter([content]), media_type="application/json; charset=utf-8")
    response.headers["Content-Disposition"] = 'attachment; filename="backup.json"'
    return response
