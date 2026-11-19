"""Database tables for shared meal groups, memberships, and pooled group orders."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.clock import utc_now


class MealGroup(SQLModel, table=True):
    __tablename__ = "meal_group"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=100, index=True)
    description: Optional[str] = Field(default=None, max_length=255)
    owner_id: int = Field(foreign_key="app_user.id", index=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GroupMember(SQLModel, table=True):
    __tablename__ = "group_member"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="meal_group.id", index=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    role: str = Field(default="member", max_length=20)  # "owner" or "member"
    # Fine-grained group permissions:
    can_create: bool = Field(default=True)   # add items/orders to the shared pool
    can_edit: bool = Field(default=False)    # update items/quantities
    can_assign: bool = Field(default=False)  # assign items/dishes to members
    joined_at: datetime = Field(default_factory=utc_now)


class GroupOrder(SQLModel, table=True):
    __tablename__ = "group_order"

    id: int | None = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="meal_group.id", index=True)
    creator_id: int = Field(foreign_key="app_user.id", index=True)
    title: str = Field(max_length=100)
    notes: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="open", max_length=20)  # open, placed, cancelled
    total: float = Field(default=0.0)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class GroupOrderItem(SQLModel, table=True):
    __tablename__ = "group_order_item"

    id: int | None = Field(default=None, primary_key=True)
    group_order_id: int = Field(foreign_key="group_order.id", index=True)
    menu_item_id: int = Field(foreign_key="menu_item.id", index=True)
    name: str = Field(max_length=100)
    unit_price: float
    quantity: int = Field(default=1)
    added_by_id: int = Field(foreign_key="app_user.id", index=True)
    assigned_to_id: Optional[int] = Field(default=None, foreign_key="app_user.id", index=True)
    notes: Optional[str] = Field(default=None, max_length=100)
