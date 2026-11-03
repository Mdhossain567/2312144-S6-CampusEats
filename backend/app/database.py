"""Database engine and session dependency."""
from collections.abc import Generator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.pool import NullPool
from sqlmodel import Session, SQLModel, create_engine

from app.config import DATABASE_URL

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


def init_db() -> None:
    """Create the tables that do not exist yet."""
    import app.menu_items.models  # noqa: F401  (registers the table)

    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]