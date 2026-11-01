"""Request and response shapes for menu items."""
from datetime import datetime
from typing import Literal

from pydantic import field_validator, model_validator
from sqlmodel import Field, SQLModel

Category = Literal["meal", "snack", "drink", "dessert"]


class MenuItemCreate(SQLModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float = Field(gt=0)
    category: Category
    is_available: bool = True

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value


class MenuItemUpdate(SQLModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    price: float | None = Field(default=None, gt=0)
    category: Category | None = None
    is_available: bool | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value):
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def reject_null_required_fields(self):
        for field in ("name", "price", "category", "is_available"):
            if field in self.model_fields_set and getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null")
        return self


class MenuItemRead(SQLModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str
    is_available: bool
    created_at: datetime
    updated_at: datetime

class MenuItemPage(SQLModel):
    items: list[MenuItemRead]
    total: int
    offset: int
    limit: int