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


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET")
    if secret:
        return secret
    if os.getenv("VERCEL"):
        # Never run in production with a secret that everybody can read in the code.
        raise RuntimeError("JWT_SECRET must be set in the Vercel environment variables")
    return "campuseats-local-development-secret-0123456789"


# Signs the access tokens. Required on Vercel; a fixed value is used locally.
JWT_SECRET = _jwt_secret()
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "15"))
REFRESH_TOKEN_DAYS = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))