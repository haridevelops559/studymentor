from datetime import datetime, timezone

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
    sessions = await get_collection("study_sessions").find(
        {"user_id": user_id}
    )

    today = datetime.now(timezone.utc).date()

    today_sessions = [
        session
        for session in sessions
        if session.get("ended_at")
        and (
            session["ended_at"].date()
            if isinstance(session["ended_at"], datetime)
            else datetime.fromisoformat(session["ended_at"]).date()
        )
        == today
    ]

    minutes_studied = sum(
        (session.get("duration_seconds") or 0)
        for session in today_sessions
    ) // 60

    reviews_done_today = sum(
        session.get("questions_attempted", 0)
        for session in today_sessions
    )

    correct_today = sum(
        session.get("questions_correct", 0)
        for session in today_sessions
    )

    recall_pct = (
        round(100 * correct_today / reviews_done_today, 1)
        if reviews_done_today
        else 0.0
    )

    topics_touched_today = len(
        {
            topic
            for session in today_sessions
            for topic in session.get("topics_reviewed", [])
        }
    )

    return {
        "minutes_studied_today": minutes_studied,
        "reviews_completed_today": reviews_done_today,
        "recall_percent_today": recall_pct,
        "topics_touched_today": topics_touched_today,
        "due": due_counts(questions),
        "retention_by_topic": topic_retention(questions),
        "weakest_topics": weakest_topics(questions),
    }