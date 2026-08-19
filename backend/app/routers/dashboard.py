from fastapi import APIRouter

from app.database import get_collection
from app.services.analytics import due_counts, topic_retention, weakest_topics

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("")
async def get_dashboard(user_id: str = "demo-user"):
    """
    Single aggregated payload for the dashboard: due-review counts, per-topic
    retention, weakest topics, and today's session totals. Kept as one
    endpoint so the frontend can render the whole "today" view with a
    single request.
    """
    questions = await get_collection("questions").find({})
    sessions = await get_collection("study_sessions").find({"user_id": user_id})

    today_sessions = [s for s in sessions if s.get("ended_at")]
    minutes_studied = sum(
        (s.get("duration_seconds") or 0) for s in today_sessions
    ) // 60
    reviews_done_today = sum(s.get("questions_attempted", 0) for s in today_sessions)
    correct_today = sum(s.get("questions_correct", 0) for s in today_sessions)
    recall_pct = (
        round(100 * correct_today / reviews_done_today, 1)
        if reviews_done_today
        else 0.0
    )

    return {
        "minutes_studied_today": minutes_studied,
        "reviews_completed_today": reviews_done_today,
        "recall_percent_today": recall_pct,
        "topics_touched_today": len({t for s in today_sessions for t in s.get("topics_reviewed", [])}),
        "due": due_counts(questions),
        "retention_by_topic": topic_retention(questions),
        "weakest_topics": weakest_topics(questions),
    }
