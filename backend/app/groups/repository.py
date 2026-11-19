"""Database queries and mutations for Meal Groups, Members, and Group Orders."""
from typing import Optional

from sqlmodel import Session, col, select

from app.groups.models import GroupMember, GroupOrder, GroupOrderItem, MealGroup
from app.users.models import AppUser


def get_group(session: Session, group_id: int) -> MealGroup | None:
    return session.get(MealGroup, group_id)


def list_user_groups(session: Session, user_id: int) -> list[MealGroup]:
    """Return groups the user is a member of (including owned groups)."""
    statement = (
        select(MealGroup)
        .join(GroupMember, GroupMember.group_id == MealGroup.id)
        .where(GroupMember.user_id == user_id)
        .order_by(MealGroup.name)
    )
    return list(session.exec(statement).all())


def list_all_groups(session: Session) -> list[MealGroup]:
    """Admin view: list all groups across the platform."""
    return list(session.exec(select(MealGroup).order_by(MealGroup.name)).all())


def save_group(session: Session, group: MealGroup) -> MealGroup:
    session.add(group)
    session.commit()
    session.refresh(group)
    return group


def delete_group(session: Session, group: MealGroup) -> None:
    # Delete all items and orders in group first
    orders = session.exec(select(GroupOrder).where(GroupOrder.group_id == group.id)).all()
    for order in orders:
        items = session.exec(
            select(GroupOrderItem).where(GroupOrderItem.group_order_id == order.id)
        ).all()
        for item in items:
            session.delete(item)
        session.delete(order)

    # Delete all members
    members = session.exec(
        select(GroupMember).where(GroupMember.group_id == group.id)
    ).all()
    for m in members:
        session.delete(m)

    session.delete(group)
    session.commit()


# ── Members ───────────────────────────────────────────────────────────────────


def get_membership(
    session: Session, group_id: int, user_id: int
) -> GroupMember | None:
    return session.exec(
        select(GroupMember).where(
            GroupMember.group_id == group_id, GroupMember.user_id == user_id
        )
    ).first()


def list_group_members(session: Session, group_id: int) -> list[GroupMember]:
    return list(
        session.exec(
            select(GroupMember).where(GroupMember.group_id == group_id)
        ).all()
    )


def count_group_members(session: Session, group_id: int) -> int:
    from sqlalchemy import func
    stmt = select(func.count(GroupMember.id)).where(GroupMember.group_id == group_id)
    return session.exec(stmt).one()


def save_member(session: Session, member: GroupMember) -> GroupMember:
    session.add(member)
    session.commit()
    session.refresh(member)
    return member


def delete_member(session: Session, member: GroupMember) -> None:
    session.delete(member)
    session.commit()


# ── Orders & Items ────────────────────────────────────────────────────────────


def get_group_order(session: Session, order_id: int) -> GroupOrder | None:
    return session.get(GroupOrder, order_id)


def list_group_orders(session: Session, group_id: int) -> list[GroupOrder]:
    return list(
        session.exec(
            select(GroupOrder)
            .where(GroupOrder.group_id == group_id)
            .order_by(GroupOrder.created_at.desc())
        ).all()
    )


def save_group_order(session: Session, order: GroupOrder) -> GroupOrder:
    session.add(order)
    session.commit()
    session.refresh(order)
    return order


def get_order_item(session: Session, item_id: int) -> GroupOrderItem | None:
    return session.get(GroupOrderItem, item_id)


def list_order_items(session: Session, group_order_id: int) -> list[GroupOrderItem]:
    return list(
        session.exec(
            select(GroupOrderItem).where(
                GroupOrderItem.group_order_id == group_order_id
            )
        ).all()
    )


def save_order_item(session: Session, item: GroupOrderItem) -> GroupOrderItem:
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_order_item(session: Session, item: GroupOrderItem) -> None:
    session.delete(item)
    session.commit()
