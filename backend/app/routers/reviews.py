from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_collection
from app.schemas.review import Review, ReviewCreate
from app.services.scheduler import is_due, next_review_date, update_difficulty

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("/today", response_model=list[Review])
async def reviews_today(user_id: str = "demo-user"):
    all_reviews = await get_collection("reviews").find({"user_id": user_id})
    today = datetime.now(timezone.utc).date()
    return [r for r in all_reviews if r["reviewed_at"].date() == today]


@router.post("", response_model=Review, status_code=201)
async def submit_review(payload: ReviewCreate):
    """
    Record a retrieval-practice attempt and reschedule the question via the
    spaced-repetition service. This is the single write path that keeps
    `questions.next_review` in sync with review history.
    """
    question = await get_collection("questions").find_one(
        {"_id": payload.question_id}
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Question not found")

    now = datetime.now(timezone.utc)
    new_difficulty = update_difficulty(question.get("difficulty", 2.5), payload.rating)
    new_next_review = next_review_date(
        payload.rating, question.get("review_count", 0), new_difficulty, now
    )

    correct_increment = 1 if payload.rating in ("good", "easy") else 0
    await get_collection("questions").update_one(
        {"_id": payload.question_id},
        {
            "last_reviewed": now,
            "next_review": new_next_review,
            "review_count": question.get("review_count", 0) + 1,
            "correct_count": question.get("correct_count", 0) + correct_increment,
            "difficulty": new_difficulty,
        },
    )

    review_doc = payload.model_dump()
    review_doc["reviewed_at"] = now
    review_doc["next_review"] = new_next_review
    created = await get_collection("reviews").insert_one(review_doc)
    return created
