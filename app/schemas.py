from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

NoteStatus = Literal[
    "draft",
    "published",
    "archived",
]


class NoteCreate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=120,
    )

    body: str = Field(
        default="",
        max_length=10000,
    )

    status: NoteStatus = "draft"


class NoteUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )

    body: str | None = Field(
        default=None,
        max_length=10000,
    )

    status: NoteStatus | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )

    id: int
    title: str
    body: str
    status: str
    created_at: datetime
    updated_at: datetime
