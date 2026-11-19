"""Request and response schemas for the Admin Dashboard."""
from datetime import datetime
from typing import Literal, Optional

from sqlmodel import Field, SQLModel

from app.users.schemas import SessionRead


class AdminStats(SQLModel):
    total_users: int
    banned_users: int
    total_orders: int
    total_menu_items: int
    total_groups: int
    new_users_7d: int
    new_orders_7d: int


class AdminUserRead(SQLModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    is_banned: bool
    banned_at: Optional[datetime]
    ban_reason: Optional[str]
    failed_logins: int
    last_login_at: Optional[datetime]
    created_at: datetime
    active_sessions_count: int = 0
    orders_count: int = 0


class AdminUserPage(SQLModel):
    items: list[AdminUserRead]
    total: int
    offset: int
    limit: int


class AdminUserDetail(AdminUserRead):
    sessions: list[SessionRead]
    recent_activity: list[dict]
    recent_orders: list[dict]
    groups: list[dict]


class BanRequest(SQLModel):
    reason: str = Field(min_length=2, max_length=500)


class RoleChangeRequest(SQLModel):
    role: Literal["customer", "kitchen_staff", "admin"]


class BulkBanRequest(SQLModel):
    user_ids: list[int]
    reason: str = Field(min_length=2, max_length=500)


class BulkUnbanRequest(SQLModel):
    user_ids: list[int]


class BulkActionResponse(SQLModel):
    affected: int
    skipped: int


class BulkDeleteRequest(SQLModel):
    type: Literal["orders", "menu", "groups"]
    ids: list[int]


class BulkDeleteResponse(SQLModel):
    deleted: int
