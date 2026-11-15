"""The app_user database table."""
from datetime import datetime

from sqlmodel import Field, SQLModel

from app.clock import utc_now


class AppUser(SQLModel, table=True):
    __tablename__ = "app_user"

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=80)
    email: str = Field(max_length=254, unique=True, index=True)
    # Argon2id hash with its own salt. The plain password is never stored.
    password_hash: str = Field(max_length=255)
    # customer, kitchen_staff or admin
    role: str = Field(default="customer", max_length=20, index=True)
    is_active: bool = Field(default=True)
    # Login lockout: counted failures and the time until which login is blocked.
    failed_logins: int = Field(default=0)
    locked_until: datetime | None = Field(default=None)
    last_login_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)