"""The user_session database table — tracks refresh tokens and active devices."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.clock import utc_now


class UserSession(SQLModel, table=True):
    __tablename__ = "user_session"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="app_user.id", index=True)
    # SHA-256 hash of the opaque refresh token stored in the cookie.
    # The raw token value is never stored in the database.
    refresh_token_hash: str = Field(max_length=64, index=True)
    # Device info recorded at login time for the session list UI.
    user_agent: Optional[str] = Field(default=None, max_length=512)
    ip_address: Optional[str] = Field(default=None, max_length=45)
    created_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime
    revoked: bool = Field(default=False)
