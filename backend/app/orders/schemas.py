"""Request and response shapes for orders."""
from datetime import datetime
from typing import Literal

from pydantic import field_validator
from sqlmodel import Field, SQLModel

OrderStatus = Literal["pending", "preparing", "ready", "completed", "cancelled"]


class OrderItemCreate(SQLModel):
    menu_item_id: int = Field(ge=1)
    quantity: int = Field(ge=1, le=20)


class OrderCreate(SQLModel):
    items: list[OrderItemCreate] = Field(min_length=1, max_length=50)

    @field_validator("items")
    @classmethod
    def each_item_once(cls, items: list[OrderItemCreate]) -> list[OrderItemCreate]:
        ids = [item.menu_item_id for item in items]
        if len(ids) != len(set(ids)):
            raise ValueError("Each menu item can appear only once; change the quantity instead")
        return items


class OrderStatusUpdate(SQLModel):
    status: OrderStatus


class OrderItemRead(SQLModel):
    id: int
    menu_item_id: int
    name: str
    unit_price: float
    quantity: int


class OrderRead(SQLModel):
    id: int
    user_id: int
    customer_name: str
    status: str
    total: float
    created_at: datetime
    updated_at: datetime
    items: list[OrderItemRead]


class OrderPage(SQLModel):
    items: list[OrderRead]
    total: int
    offset: int
    limit: int