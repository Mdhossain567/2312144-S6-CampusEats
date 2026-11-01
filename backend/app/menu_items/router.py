"""HTTP endpoints for menu items under /api/v1/menu (JSON)."""
from fastapi import APIRouter, Query, Response, status

from app.database import SessionDep
from app.menu_items import service
from app.menu_items.schemas import (
    Category,
    MenuItemCreate,
    MenuItemPage,
    MenuItemRead,
    MenuItemUpdate,
)

router = APIRouter(prefix="/api/v1/menu", tags=["menu"])


@router.post("", response_model=MenuItemRead, status_code=status.HTTP_201_CREATED)
def create_menu_item(data: MenuItemCreate, session: SessionDep):
    return service.create_menu_item(session, data)


@router.get("", response_model=MenuItemPage)
def list_menu_items(
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category: Category | None = None,
    available: bool | None = None,
    q: str | None = None,
):
    items, total = service.list_menu_items(session, offset, limit, category, available, q)
    return MenuItemPage(
        items=[MenuItemRead.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
    )


@router.get("/{menu_item_id}", response_model=MenuItemRead)
def get_menu_item(menu_item_id: int, session: SessionDep):
    return service.get_menu_item(session, menu_item_id)


@router.patch("/{menu_item_id}", response_model=MenuItemRead)
def update_menu_item(menu_item_id: int, data: MenuItemUpdate, session: SessionDep):
    return service.update_menu_item(session, menu_item_id, data)


@router.delete("/{menu_item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_menu_item(menu_item_id: int, session: SessionDep):
    service.delete_menu_item(session, menu_item_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)