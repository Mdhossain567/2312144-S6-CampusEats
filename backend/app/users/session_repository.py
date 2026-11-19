"""Database queries for UserSession. Nothing else touches the session table."""
import hashlib
import secrets
from datetime import timedelta

from sqlmodel import Session, select

from app.clock import as_utc, utc_now
from app.config import REFRESH_TOKEN_DAYS
from app.users.session_model import UserSession


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(
    db: Session,
    user_id: int,
    user_agent: str | None,
    ip_address: str | None,
) -> tuple[UserSession, str]:
    """Create a new UserSession row and return (session, raw_refresh_token).

    The raw token is set in the cookie; only its hash is stored.
    """
    raw_token = secrets.token_urlsafe(48)
    session = UserSession(
        user_id=user_id,
        refresh_token_hash=_hash(raw_token),
        user_agent=user_agent,
        ip_address=ip_address,
        expires_at=utc_now() + timedelta(days=REFRESH_TOKEN_DAYS),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, raw_token


def get_by_token(db: Session, raw_token: str) -> UserSession | None:
    token_hash = _hash(raw_token)
    return db.exec(
        select(UserSession).where(UserSession.refresh_token_hash == token_hash)
    ).first()


def rotate(db: Session, session: UserSession) -> tuple[UserSession, str]:
    """Invalidate the old token and issue a new one (token rotation)."""
    new_raw = secrets.token_urlsafe(48)
    session.refresh_token_hash = _hash(new_raw)
    session.expires_at = utc_now() + timedelta(days=REFRESH_TOKEN_DAYS)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session, new_raw


def revoke(db: Session, session: UserSession) -> None:
    session.revoked = True
    db.add(session)
    db.commit()


def list_active(db: Session, user_id: int) -> list[UserSession]:
    """Return all non-revoked, non-expired sessions for a user."""
    now = utc_now()
    rows = db.exec(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,  # noqa: E712
        )
    ).all()
    return [s for s in rows if as_utc(s.expires_at) > now]


def revoke_by_id(db: Session, session_id: int, user_id: int) -> bool:
    """Revoke a specific session owned by user_id. Returns True if found."""
    s = db.get(UserSession, session_id)
    if s is None or s.user_id != user_id:
        return False
    s.revoked = True
    db.add(s)
    db.commit()
    return True


def revoke_all_except(db: Session, user_id: int, keep_id: int) -> int:
    """Revoke every active session for user_id except keep_id. Returns count."""
    sessions = db.exec(
        select(UserSession).where(
            UserSession.user_id == user_id,
            UserSession.revoked == False,  # noqa: E712
            UserSession.id != keep_id,
        )
    ).all()
    for s in sessions:
        s.revoked = True
        db.add(s)
    db.commit()
    return len(sessions)
