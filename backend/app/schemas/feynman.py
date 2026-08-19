from datetime import datetime, timezone

from pydantic import BaseModel, Field


class FeynmanCreate(BaseModel):
    topic_id: str
    user_id: str = "demo-user"
    explanation: str = Field(..., min_length=1)
    checklist: list[str] = Field(
        default_factory=list,
        description="Key ideas the explanation should cover, for self-check.",
    )


class FeynmanCheckResult(BaseModel):
    covered: list[str]
    missing: list[str]
    coverage_ratio: float


class FeynmanExplanation(FeynmanCreate):
    id: str = Field(alias="_id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    check_result: FeynmanCheckResult

    model_config = {"populate_by_name": True}
