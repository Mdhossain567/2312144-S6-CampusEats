"""Time helpers: always work in UTC."""
from datetime import datetime, timezone


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    """SQLite returns naive datetimes; treat them as UTC so they can be compared."""
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)