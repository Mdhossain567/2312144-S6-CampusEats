"""Database queries for menu items. Nothing else touches the session."""
from sqlmodel import Session, col, func, select

from app.menu_items.models import MenuItem


def get(session: Session, menu_item_id: int) -> MenuItem | None:
    return session.get(MenuItem, menu_item_id)


def get_by_name(session: Session, name: str) -> MenuItem | None:
    return session.exec(select(MenuItem).where(MenuItem.name == name)).first()


def list_items(
    session: Session,
    offset: int,
    limit: int,
    category: str | None = None,
    available: bool | None = None,
    q: str | None = None,
) -> tuple[list[MenuItem], int]:
    query = select(MenuItem)
    if category:
        query = query.where(MenuItem.category == category)
    if available is not None:
        query = query.where(MenuItem.is_available == available)
    if q:
        query = query.where(col(MenuItem.name).ilike(f"%{q}%"))

    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    items = session.exec(
        query.order_by(col(MenuItem.id).desc()).offset(offset).limit(limit)
    ).all()
    return list(items), total


def save(session: Session, item: MenuItem) -> MenuItem:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete(session: Session, item: MenuItem) -> None:
    session.delete(item)
    session.commit()