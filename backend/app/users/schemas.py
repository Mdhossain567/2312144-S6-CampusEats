"""Request and response shapes for accounts and login."""
from datetime import datetime
from typing import Literal, Optional

from pydantic import EmailStr, field_validator
from sqlmodel import Field, SQLModel

Role = Literal["customer", "kitchen_staff", "admin"]


class UserRegister(SQLModel):
    name: str = Field(min_length=2, max_length=80)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def password_needs_letter_and_digit(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one digit")
        return value


class UserLogin(SQLModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) else value


class UserRead(SQLModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool
    is_banned: bool
    created_at: datetime


class TokenResponse(SQLModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRead


class ProfileUpdate(SQLModel):
    """Fields a user may update on their own profile."""
    name: Optional[str] = Field(default=None, min_length=2, max_length=80)
    email: Optional[EmailStr] = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) and value else value

    @field_validator("email", mode="before")
    @classmethod
    def clean_email(cls, value):
        return value.strip().lower() if isinstance(value, str) and value else value


class PasswordChange(SQLModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def password_needs_letter_and_digit(cls, value: str) -> str:
        if not any(c.isalpha() for c in value) or not any(c.isdigit() for c in value):
            raise ValueError("Password must contain at least one letter and one digit")
        return value


class SessionRead(SQLModel):
    id: int
    user_agent: Optional[str]
    ip_address: Optional[str]
    created_at: datetime
    expires_at: datetime
    is_current: bool
