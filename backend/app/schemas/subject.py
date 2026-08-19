from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SubjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = Field(default=None, max_length=500)


class Subject(SubjectCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = {"populate_by_name": True}


class TopicCreate(BaseModel):
    subject_id: str
    name: str = Field(..., min_length=1, max_length=120)


class Topic(TopicCreate):
    id: str = Field(alias="_id")

    model_config = {"populate_by_name": True}
