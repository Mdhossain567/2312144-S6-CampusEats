"""The audit_log database table."""
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.clock import utc_now


class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, index=True)
    user_email: Optional[str] = Field(default=None, max_length=254)
    action: str = Field(max_length=50, index=True)
    resource_type: Optional[str] = Field(default=None, max_length=50)
    resource_id: Optional[str] = Field(default=None, max_length=100)
    ip_address: Optional[str] = Field(default=None, max_length=45, index=True)
    user_agent: Optional[str] = Field(default=None, max_length=512)
    details: Optional[str] = Field(default=None, max_length=1000)
    created_at: datetime = Field(default_factory=utc_now, index=True)
