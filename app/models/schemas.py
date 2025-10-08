from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ColumnType(str, Enum):
    BACKLOG = "backlog"
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class CardBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    column: ColumnType

    model_config = ConfigDict(use_enum_values=True)


class CardCreate(CardBase):
    pass


class CardUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    column: Optional[ColumnType] = None

    model_config = ConfigDict(use_enum_values=True)


# class CardMove(BaseModel):
#     target_column: ColumnType
#     new_order_idx: int


class CardResponse(CardBase):
    id: int
    order_idx: int
    created_at: datetime
    updated_at: datetime
