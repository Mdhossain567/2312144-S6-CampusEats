"""Database queries for orders. Nothing else touches the session."""
from sqlmodel import Session, col, func, select

from app.orders.models import CustomerOrder, OrderItem
from app.users.models import AppUser


def create(session: Session, order: CustomerOrder, items: list[OrderItem]) -> CustomerOrder:
    session.add(order)
    session.flush()  # gives the order its id
    for item in items:
        item.order_id = order.id
        session.add(item)
    session.commit()
    session.refresh(order)
    return order


def get(session: Session, order_id: int) -> CustomerOrder | None:
    return session.get(CustomerOrder, order_id)


def save(session: Session, order: CustomerOrder) -> CustomerOrder:
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def list_orders(
    session: Session,
    offset: int,
    limit: int,
    user_id: int | None = None,
    status: str | None = None,
) -> tuple[list[CustomerOrder], int]:
    query = select(CustomerOrder)
    if user_id is not None:
        query = query.where(CustomerOrder.user_id == user_id)
    if status:
        query = query.where(CustomerOrder.status == status)

    total = session.exec(select(func.count()).select_from(query.subquery())).one()
    orders = session.exec(
        query.order_by(col(CustomerOrder.id).desc()).offset(offset).limit(limit)
    ).all()
    return list(orders), total


def items_by_order(session: Session, order_ids: list[int]) -> dict[int, list[OrderItem]]:
    result: dict[int, list[OrderItem]] = {order_id: [] for order_id in order_ids}
    if not order_ids:
        return result
    rows = session.exec(
        select(OrderItem)
        .where(col(OrderItem.order_id).in_(order_ids))
        .order_by(col(OrderItem.id))
    ).all()
    for row in rows:
        result[row.order_id].append(row)
    return result


def customer_names(session: Session, user_ids: list[int]) -> dict[int, str]:
    if not user_ids:
        return {}
    rows = session.exec(
        select(AppUser.id, AppUser.name).where(col(AppUser.id).in_(user_ids))
    ).all()
    return {user_id: name for user_id, name in rows}


def menu_item_is_used(session: Session, menu_item_id: int) -> bool:
    found = session.exec(
        select(OrderItem.id).where(OrderItem.menu_item_id == menu_item_id).limit(1)
    ).first()
    return found is not None