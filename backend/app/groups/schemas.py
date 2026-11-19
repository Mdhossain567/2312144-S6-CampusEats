"""Request and response schemas for Meal Groups, Members, and Group Orders."""
from datetime import datetime
from typing import Optional

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel


class GroupCreate(SQLModel):
    name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class GroupUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)


class GroupMemberAdd(SQLModel):
    email: EmailStr
    can_create: bool = True
    can_edit: bool = False
    can_assign: bool = False

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class GroupMemberUpdate(SQLModel):
    can_create: Optional[bool] = None
    can_edit: Optional[bool] = None
    can_assign: Optional[bool] = None


class GroupMemberRead(SQLModel):
    id: int
    group_id: int
    user_id: int
    user_name: str
    user_email: str
    role: str
    can_create: bool
    can_edit: bool
    can_assign: bool
    joined_at: datetime


class GroupOrderItemCreate(SQLModel):
    menu_item_id: int
    quantity: int = Field(default=1, ge=1, le=50)
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=100)


class GroupOrderItemUpdate(SQLModel):
    quantity: Optional[int] = Field(default=None, ge=1, le=50)
    assigned_to_id: Optional[int] = None
    notes: Optional[str] = Field(default=None, max_length=100)


class GroupOrderItemRead(SQLModel):
    id: int
    group_order_id: int
    menu_item_id: int
    name: str
    unit_price: float
    quantity: int
    subtotal: float
    added_by_id: int
    added_by_name: str
    assigned_to_id: Optional[int]
    assigned_to_name: Optional[str]
    notes: Optional[str]


class GroupOrderCreate(SQLModel):
    title: str = Field(min_length=2, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=255)
    items: list[GroupOrderItemCreate] = Field(default_factory=list)


class GroupOrderRead(SQLModel):
    id: int
    group_id: int
    creator_id: int
    creator_name: str
    title: str
    notes: Optional[str]
    status: str
    total: float
    items: list[GroupOrderItemRead]
    created_at: datetime
    updated_at: datetime


class GroupPermissions(SQLModel):
    is_owner: bool
    can_create: bool
    can_edit: bool
    can_assign: bool


class GroupRead(SQLModel):
    id: int
    name: str
    description: Optional[str]
    owner_id: int
    owner_name: str
    members_count: int
    created_at: datetime
    my_role: Optional[str] = None
    my_permissions: Optional[GroupPermissions] = None


class GroupDetailRead(GroupRead):
    members: list[GroupMemberRead]
    orders: list[GroupOrderRead]
