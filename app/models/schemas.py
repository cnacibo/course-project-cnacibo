import json
import re
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

ALLOWED_TEXT_REGEX = re.compile(r"^[^\x00-\x1F\x7F]*$")


def validate_text_chars(value: str, field_name: str):
    if value is None:
        return value
    if not ALLOWED_TEXT_REGEX.match(value):
        raise ValueError(f"{field_name} contains invalid control characters")
    return value


class StripAndValidateMixin:
    @classmethod
    @field_validator("title", "description", mode="before")
    def strip_and_validate(cls, v, info):
        if v is None:
            return v
        if isinstance(v, str):
            v = v.strip()
            if info.field_name == "title" and not v:
                raise ValueError("title cannot be empty or whitespace only")
        return v

    @classmethod
    @field_validator("title", "description", mode="after")
    def validate_allowed_chars_after(cls, v, info):
        return validate_text_chars(v, info.field_name)


class ColumnType(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class CardBase(StripAndValidateMixin, BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    column: ColumnType

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class CardCreate(CardBase):
    pass


class CardUpdate(StripAndValidateMixin, BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=1000)
    column: Optional[ColumnType] = None

    model_config = ConfigDict(use_enum_values=True, extra="forbid")


class CardResponse(CardBase):
    id: int
    order_idx: int
    created_at: datetime
    updated_at: datetime

    @classmethod
    @field_validator("created_at", "updated_at", mode="before")
    def normalize_datetime(cls, v):
        if isinstance(v, datetime) and v.tzinfo is not None:
            return v.astimezone(timezone.utc).replace(tzinfo=None)
        return v


def safe_json_parse(json_str: str):
    return json.loads(json_str, parse_float=Decimal, parse_int=Decimal)
