"""
Tools.

Concept being explored: a LangChain/LangGraph "tool" is just a typed Python
function the LLM can choose to call (function calling under the hood) --
the LLM decides *when* to call it and *what arguments* to pass, based on
the tool's name/description/schema.

Deliberately, these tools don't hit the network or a real LLM -- they wrap
the app's own already-tested pure functions
(`app/services/scheduler.py`, `app/services/analytics.py`), so an agent
built on top of them inherits correctness you already verified with
`pytest`, instead of asking the LLM to "do spaced-repetition math" itself
(which LLMs are unreliable at).

Run: python -m app.agents.tools
"""
from __future__ import annotations

from datetime import datetime, timezone

from langchain_core.tools import tool

from app.services.scheduler import next_review_date, update_difficulty
from app.schemas.review import ReviewRating


@tool
def compute_next_review(rating: str, review_count: int, difficulty: float) -> str:
    """
    Given a recall rating ('again', 'hard', 'good', or 'easy'), the number
    of times a question has been reviewed, and its current ease factor,
    return the next review date as an ISO 8601 string. Use this instead of
    estimating spaced-repetition intervals yourself.
    """
    rating_enum = ReviewRating(rating)
    now = datetime.now(timezone.utc)
    new_difficulty = update_difficulty(difficulty, rating_enum)
    next_date = next_review_date(rating_enum, review_count, new_difficulty, now)
    return next_date.isoformat()


@tool
def summarize_weak_topics(retention_by_topic: dict[str, float]) -> str:
    """
    Given a mapping of topic name to retention percentage, return a short
    plain-text summary of which topics need the most attention. Use this to
    turn raw dashboard numbers into a sentence a student can act on.
    """
    if not retention_by_topic:
        return "No retention data yet -- nothing to flag."
    ranked = sorted(retention_by_topic.items(), key=lambda kv: kv[1])
    weakest = ranked[0]
    return (
        f"Focus on '{weakest[0]}' next -- it's at {weakest[1]}% retention, "
        f"the lowest of {len(retention_by_topic)} tracked topics."
    )


AVAILABLE_TOOLS = [compute_next_review, summarize_weak_topics]


if __name__ == "__main__":
    result = compute_next_review.invoke(
        {"rating": "good", "review_count": 2, "difficulty": 2.5}
    )
    print("compute_next_review ->", result)

    result2 = summarize_weak_topics.invoke(
        {"retention_by_topic": {"React Hooks": 82.0, "Operating Systems": 54.0}}
    )
    print("summarize_weak_topics ->", result2)
