from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.actions import router as actions_router
from app.api.admin import router as admin_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.interactions import router as interactions_router
from app.api.ratings import router as ratings_router
from app.api.recommendations import router as recommendations_router
from app.api.search_history import router as search_history_router
from app.api.users import router as users_router
from app.core.bootstrap import (
    ensure_admin_user,
    ensure_document_table_columns,
    ensure_user_table_columns,
    sync_document_id_sequence,
)
from app.core.database import Base, engine, get_db
from app.core.runtime_logs import log_error_event, log_failed_request

ensure_user_table_columns()
ensure_document_table_columns()
Base.metadata.create_all(bind=engine)
sync_document_id_sequence()

app = FastAPI(
    title="VKR Library Recommender",
    description="Academic library prototype with admin tools and recommendations",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://172.18.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        if response.status_code >= 400:
            log_failed_request(request.url.path, request.method, response.status_code)
        return response
    except Exception as exc:  # pragma: no cover - defensive runtime logging
        log_error_event(request.url.path, request.method, str(exc))
        log_failed_request(request.url.path, request.method, 500, str(exc))
        return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(documents_router)
app.include_router(users_router)
app.include_router(interactions_router)
app.include_router(ratings_router)
app.include_router(search_history_router)
app.include_router(recommendations_router)
app.include_router(analytics_router)
app.include_router(actions_router)
app.include_router(auth_router)
app.include_router(admin_router)


@app.on_event("startup")
def bootstrap_admin() -> None:
    db: Session = next(get_db())
    try:
        ensure_admin_user(db)
    finally:
        db.close()


@app.get("/")
def root():
    return {"message": "VKR backend works"}


@app.get("/health")
def health_check():
    return {"status": "ok"}

