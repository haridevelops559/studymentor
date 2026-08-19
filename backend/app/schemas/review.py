from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class ReviewRating(str, Enum):
    again = "again"
    hard = "hard"
    good = "good"
    easy = "easy"


class ReviewCreate(BaseModel):
    question_id: str
    user_id: str = "demo-user"
    rating: ReviewRating
    given_answer: str = Field(default="", max_length=2000)


class Review(ReviewCreate):
    id: str = Field(alias="_id")
    reviewed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    next_review: datetime

    model_config = {"populate_by_name": True}
