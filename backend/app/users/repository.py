"""Database queries for accounts. Nothing else touches the session."""
from sqlmodel import Session, select

from app.users.models import AppUser


def get(session: Session, user_id: int) -> AppUser | None:
    return session.get(AppUser, user_id)


def get_by_email(session: Session, email: str) -> AppUser | None:
    return session.exec(select(AppUser).where(AppUser.email == email)).first()


def save(session: Session, user: AppUser) -> AppUser:
    session.add(user)
    session.commit()
    session.refresh(user)
    return user