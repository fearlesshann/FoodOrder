from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    created_at: datetime
    updated_at: datetime


class CategoryWrite(BaseModel):
    name: str = Field(min_length=1, max_length=20)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("分类名不能为空")
        return cleaned


class CatalogDishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    image_url: str
    sort_order: int
    category: CategoryRead
    created_at: datetime
    updated_at: datetime


class SelectionNoteUpdate(BaseModel):
    note: str = Field(default="", max_length=120)

    @field_validator("note")
    @classmethod
    def clean_note(cls, value: str) -> str:
        return value.strip()


class SelectionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dinner_date: date
    note: str
    created_at: datetime
    updated_at: datetime
    dish: CatalogDishRead


class MenuRead(BaseModel):
    dinner_date: date
    selections: list[SelectionRead]
