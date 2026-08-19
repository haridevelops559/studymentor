from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class SessionStart(BaseModel):
    user_id: str = "demo-user"
    planned_activities: list[str] = Field(default_factory=list)


class SessionFinish(BaseModel):
    questions_attempted: int = 0
    questions_correct: int = 0
    topics_reviewed: list[str] = Field(default_factory=list)


class StudySession(BaseModel):
    id: str = Field(alias="_id")
    user_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    planned_activities: list[str] = Field(default_factory=list)
    questions_attempted: int = 0
    questions_correct: int = 0
    topics_reviewed: list[str] = Field(default_factory=list)

    model_config = {"populate_by_name": True}
