"""Business rules for menu items."""
from fastapi import HTTPException, status
from sqlmodel import Session

from app.menu_items import repository
from app.menu_items.models import MenuItem, utc_now
from app.menu_items.schemas import MenuItemCreate, MenuItemUpdate
from app.orders import repository as order_repository


def _duplicate_name() -> HTTPException:
    return HTTPException(status.HTTP_409_CONFLICT, "A menu item with this name already exists")


def create_menu_item(session: Session, data: MenuItemCreate) -> MenuItem:
    if repository.get_by_name(session, data.name):
        raise _duplicate_name()
    return repository.save(session, MenuItem(**data.model_dump()))


def list_menu_items(session, offset, limit, category, available, q):
    return repository.list_items(session, offset, limit, category, available, q)


def get_menu_item(session: Session, menu_item_id: int) -> MenuItem:
    item = repository.get(session, menu_item_id)
    if item is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Menu item not found")
    return item


def update_menu_item(session: Session, menu_item_id: int, data: MenuItemUpdate) -> MenuItem:
    item = get_menu_item(session, menu_item_id)
    changes = data.model_dump(exclude_unset=True)

    new_name = changes.get("name")
    if new_name and new_name != item.name and repository.get_by_name(session, new_name):
        raise _duplicate_name()

    for field, value in changes.items():
        setattr(item, field, value)
    item.updated_at = utc_now()
    return repository.save(session, item)


def delete_menu_item(session: Session, menu_item_id: int) -> None:
    item = get_menu_item(session, menu_item_id)
    # Old orders keep pointing at the item, so it cannot be removed.
    if order_repository.menu_item_is_used(session, menu_item_id):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "This menu item is part of an order. Mark it unavailable instead of deleting it.",
        )
    repository.delete(session, item)