from __future__ import annotations

import re
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


FAMILY_CODE_PATTERN = re.compile(r"^[A-Za-z0-9_-]{6,48}$")


def validate_family_code(value: str) -> str:
    if not FAMILY_CODE_PATTERN.fullmatch(value):
        raise ValueError("家庭码需为 6–48 位字母、数字、下划线或连字符")
    return value


class DishCreate(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    ordered_by: str = Field(min_length=1, max_length=24)
    dinner_date: date | None = None

    @field_validator("name", "ordered_by")
    @classmethod
    def clean_text(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("内容不能为空")
        return cleaned


class DishUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=40)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("菜名不能为空")
        return cleaned


class DishRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    ordered_by: str
    dinner_date: date
    created_at: datetime
    updated_at: datetime


class MenuRead(BaseModel):
    family_code: str
    dinner_date: date
    dishes: list[DishRead]

