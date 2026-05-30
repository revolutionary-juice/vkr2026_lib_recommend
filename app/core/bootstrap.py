from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.core.database import engine
from app.core.security import hash_password
from app.models.user import User


def ensure_user_table_columns() -> None:
    inspector = inspect(engine)
    if "users" not in inspector.get_table_names():
        return

    user_columns = {column["name"] for column in inspector.get_columns("users")}
    if "is_blocked" in user_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE users ADD COLUMN is_blocked INTEGER NOT NULL DEFAULT 0"))


def ensure_document_table_columns() -> None:
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    document_columns = {column["name"] for column in inspector.get_columns("documents")}
    columns_to_add = {
        "publisher": "ALTER TABLE documents ADD COLUMN publisher VARCHAR",
        "isbn": "ALTER TABLE documents ADD COLUMN isbn VARCHAR",
        "udk": "ALTER TABLE documents ADD COLUMN udk VARCHAR",
        "bbk": "ALTER TABLE documents ADD COLUMN bbk VARCHAR",
        "rubrics": "ALTER TABLE documents ADD COLUMN rubrics TEXT",
        "source_url": "ALTER TABLE documents ADD COLUMN source_url VARCHAR",
        "source_system": "ALTER TABLE documents ADD COLUMN source_system VARCHAR",
        "external_id": "ALTER TABLE documents ADD COLUMN external_id VARCHAR",
        "has_fulltext": "ALTER TABLE documents ADD COLUMN has_fulltext INTEGER NOT NULL DEFAULT 0",
    }

    with engine.begin() as connection:
        for column_name, alter_sql in columns_to_add.items():
            if column_name not in document_columns:
                connection.execute(text(alter_sql))


def sync_document_id_sequence() -> None:
    inspector = inspect(engine)
    if "documents" not in inspector.get_table_names():
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                SELECT setval(
                    pg_get_serial_sequence('documents', 'id'),
                    COALESCE((SELECT MAX(id) FROM documents), 1),
                    true
                )
                """
            )
        )


def ensure_admin_user(db: Session) -> None:
    admin = db.query(User).filter(User.username == "admin").first()
    if admin:
        admin.email = "admin@example.com"
        admin.password_hash = hash_password("admin")
        admin.role = "admin"
        admin.is_blocked = 0
        db.commit()
        return

    admin = User(
        username="admin",
        email="admin@example.com",
        password_hash=hash_password("admin"),
        role="admin",
        is_blocked=0,
    )
    db.add(admin)
    db.commit()
