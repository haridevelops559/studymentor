from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class QuestionType(str, Enum):
    recall = "recall"
    cloze = "cloze"
    application = "application"


class QuestionCreate(BaseModel):
    topic_id: str
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)
    type: QuestionType = QuestionType.recall


class Question(QuestionCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Scheduling state, owned by the spaced-repetition scheduler.
    last_reviewed: Optional[datetime] = None
    next_review: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    review_count: int = 0
    correct_count: int = 0
    difficulty: float = 2.5  # ease factor, SM-2-inspired

    model_config = {"populate_by_name": True}
