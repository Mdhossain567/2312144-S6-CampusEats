"""Business rules for orders."""
from fastapi import HTTPException, status
from sqlmodel import Session

from app.clock import utc_now
from app.menu_items import repository as menu_repository
from app.orders import repository
from app.orders.models import (
    CANCELLED,
    COMPLETED,
    PENDING,
    PREPARING,
    READY,
    CustomerOrder,
    OrderItem,
)
from app.orders.schemas import OrderCreate, OrderItemRead, OrderPage, OrderRead
from app.users.models import AppUser

# Which step may follow which. Anything else is rejected with 409.
TRANSITIONS: dict[str, set[str]] = {
    PENDING: {PREPARING, CANCELLED},
    PREPARING: {READY},
    READY: {COMPLETED},
    COMPLETED: set(),
    CANCELLED: set(),
}


def _not_found() -> HTTPException:
    return HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")


def _build_reads(session: Session, orders: list[CustomerOrder]) -> list[OrderRead]:
    items = repository.items_by_order(session, [order.id for order in orders])
    names = repository.customer_names(session, list({order.user_id for order in orders}))
    return [
        OrderRead(
            id=order.id,
            user_id=order.user_id,
            customer_name=names.get(order.user_id, "Unknown"),
            status=order.status,
            total=order.total,
            created_at=order.created_at,
            updated_at=order.updated_at,
            items=[OrderItemRead.model_validate(item) for item in items[order.id]],
        )
        for order in orders
    ]


def place_order(session: Session, user: AppUser, data: OrderCreate) -> OrderRead:
    lines: list[OrderItem] = []
    total = 0.0

    for entry in data.items:
        menu_item = menu_repository.get(session, entry.menu_item_id)
        if menu_item is None:
            raise HTTPException(422, f"Menu item {entry.menu_item_id} does not exist")
        if not menu_item.is_available:
            raise HTTPException(422, f"{menu_item.name} is not available")

        # The price always comes from the menu, never from the client.
        total += menu_item.price * entry.quantity
        lines.append(
            OrderItem(
                order_id=0,
                menu_item_id=menu_item.id,
                name=menu_item.name,
                unit_price=menu_item.price,
                quantity=entry.quantity,
            )
        )

    order = CustomerOrder(user_id=user.id, status=PENDING, total=round(total, 2))
    repository.create(session, order, lines)
    return _build_reads(session, [order])[0]


def list_my_orders(session: Session, user: AppUser, offset: int, limit: int) -> OrderPage:
    orders, total = repository.list_orders(session, offset, limit, user_id=user.id)
    return OrderPage(items=_build_reads(session, orders), total=total, offset=offset, limit=limit)


def list_all_orders(
    session: Session, offset: int, limit: int, status_filter: str | None
) -> OrderPage:
    orders, total = repository.list_orders(session, offset, limit, status=status_filter)
    return OrderPage(items=_build_reads(session, orders), total=total, offset=offset, limit=limit)


def get_order(session: Session, user: AppUser, order_id: int) -> OrderRead:
    order = repository.get(session, order_id)
    # A customer asking for somebody else's order gets the same answer as for a
    # missing order, so they cannot even tell that it exists.
    if order is None or (user.role == "customer" and order.user_id != user.id):
        raise _not_found()
    return _build_reads(session, [order])[0]


def update_status(session: Session, order_id: int, new_status: str) -> OrderRead:
    order = repository.get(session, order_id)
    if order is None:
        raise _not_found()

    if new_status not in TRANSITIONS.get(order.status, set()):
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Cannot change an order from {order.status} to {new_status}",
        )

    order.status = new_status
    order.updated_at = utc_now()
    repository.save(session, order)
    return _build_reads(session, [order])[0]


def cancel_order(session: Session, user: AppUser, order_id: int) -> OrderRead:
    order = repository.get(session, order_id)
    if order is None or (user.role != "admin" and order.user_id != user.id):
        raise _not_found()

    if order.status != PENDING:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only a pending order can be cancelled")

    order.status = CANCELLED
    order.updated_at = utc_now()
    repository.save(session, order)
    return _build_reads(session, [order])[0]