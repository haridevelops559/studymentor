from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class NoteCreate(BaseModel):
    topic_id: str
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    cues: list[str] = Field(default_factory=list)
    summary: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    cues: Optional[list[str]] = None
    summary: Optional[str] = None


class Note(NoteCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}
