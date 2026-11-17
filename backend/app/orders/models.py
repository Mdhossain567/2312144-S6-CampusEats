"""The customer_order and order_item database tables."""
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.clock import utc_now

# The steps of an order. Allowed moves between them are in orders/service.py.
PENDING = "pending"
PREPARING = "preparing"
READY = "ready"
COMPLETED = "completed"
CANCELLED = "cancelled"


class CustomerOrder(SQLModel, table=True):
    # "order" is a reserved word in SQL, so the table has a longer name.
    __tablename__ = "customer_order"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    status: str = Field(default=PENDING, max_length=20, index=True)
    total: float
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class OrderItem(SQLModel, table=True):
    __tablename__ = "order_item"

    id: int | None = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="customer_order.id", index=True)
    menu_item_id: int = Field(foreign_key="menu_item.id", index=True)
    # The name and the price are copied when the order is placed, so changing the
    # menu later does not change old orders.
    name: str = Field(max_length=100)
    unit_price: float
    quantity: int