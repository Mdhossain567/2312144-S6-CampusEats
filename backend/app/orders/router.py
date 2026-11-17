"""HTTP endpoints for orders under /api/v1/orders (JSON)."""
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.auth.dependencies import CurrentUser, require_roles
from app.database import SessionDep
from app.orders import service
from app.orders.schemas import (
    OrderCreate,
    OrderPage,
    OrderRead,
    OrderStatus,
    OrderStatusUpdate,
)
from app.users.models import AppUser

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])

# 401 without a valid token, 403 for any other role.
CustomerUser = Annotated[AppUser, Depends(require_roles("customer"))]
CustomerOrAdmin = Annotated[AppUser, Depends(require_roles("customer", "admin"))]
StaffUser = Annotated[AppUser, Depends(require_roles("kitchen_staff", "admin"))]


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def place_order(data: OrderCreate, user: CustomerUser, session: SessionDep):
    return service.place_order(session, user, data)


# "/my" is declared before "/{order_id}" so that "my" is not read as an id.
@router.get("/my", response_model=OrderPage)
def my_orders(
    user: CustomerUser,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    return service.list_my_orders(session, user, offset, limit)


@router.get("", response_model=OrderPage)
def all_orders(
    user: StaffUser,
    session: SessionDep,
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: OrderStatus | None = Query(None, alias="status"),
):
    return service.list_all_orders(session, offset, limit, status_filter)


@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, user: CurrentUser, session: SessionDep):
    return service.get_order(session, user, order_id)


@router.patch("/{order_id}/status", response_model=OrderRead)
def change_status(
    order_id: int, data: OrderStatusUpdate, user: StaffUser, session: SessionDep
):
    return service.update_status(session, order_id, data.status)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_order(order_id: int, user: CustomerOrAdmin, session: SessionDep):
    return service.cancel_order(session, user, order_id)