"""App settings, read from environment variables."""
import os


def _normalize(url: str) -> str:
    """Hosted Postgres URLs start with postgres://; SQLAlchemy needs a driver name."""
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


# Local default is a SQLite file; in production set DATABASE_URL (Supabase).
DATABASE_URL = _normalize(
    os.getenv("DATABASE_URL")
    or os.getenv("POSTGRES_URL")
    or "sqlite:///./campuseats.db"
)