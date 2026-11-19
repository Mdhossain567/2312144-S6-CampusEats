"""Database engine and session dependency."""
import logging
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

logger = logging.getLogger("campuseats")

if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    # Supabase transaction pooler (port 6543): no client-side pool and no
    # prepared statements, because the pooler hands out a new connection per query.
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,
        connect_args={"prepare_threshold": None},
    )


def _safe_add_column(conn, table: str, column: str, definition: str) -> None:
    """Add a column if it does not already exist (SQLite and Postgres compat)."""
    is_sqlite = DATABASE_URL.startswith("sqlite")
    if is_sqlite:
        # SQLite does not support IF NOT EXISTS on ALTER TABLE;
        # check the pragma instead.
        rows = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
        existing = {row[1] for row in rows}
        if column not in existing:
            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
    else:
        # PostgreSQL supports IF NOT EXISTS.
        conn.execute(
            text(
                f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column} {definition}"
            )
        )


def _migrate(conn) -> None:
    """Add any new columns that existing databases are missing."""
    # app_user ban fields (added in auth-sessions-and-ban)
    _safe_add_column(conn, "app_user", "is_banned", "BOOLEAN NOT NULL DEFAULT FALSE")
    _safe_add_column(conn, "app_user", "banned_at", "TIMESTAMP")
    _safe_add_column(conn, "app_user", "ban_reason", "VARCHAR(500)")


def init_db() -> None:
    """Create the tables that do not exist yet, then apply safe column migrations."""
    import app.menu_items.models  # noqa: F401  (registers the table)
    import app.orders.models  # noqa: F401  (registers the tables)
    import app.users.models  # noqa: F401  (registers the table)
    import app.users.session_model  # noqa: F401  (registers the table)

    SQLModel.metadata.create_all(engine)

    # Safely add columns that were introduced after the initial schema so that
    # existing Supabase / SQLite databases do not break on upgrade.
    with engine.begin() as conn:
        try:
            _migrate(conn)
        except Exception:
            logger.exception("Could not apply column migrations (non-fatal)")


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
