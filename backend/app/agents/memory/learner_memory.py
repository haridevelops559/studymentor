"""
Persistent learner memory for StudyMentor.

This service converts the backend's durable learning history into the
structured `learning_state` consumed by the adaptive agent.

Important architectural boundary:

    Database
        ↓
    Learner memory service
        ↓
    LangGraph state
        ↓
    Adaptive planner

The graph should not query MongoDB directly.
"""

from __future__ import annotations

from typing import Any

from app.database import get_collection
from app.services.analytics import (
    due_counts,
    topic_retention,
    weakest_topics,
)


async def build_learner_memory(
    user_id: str = "demo-user",
) -> dict[str, Any]:
    """
    Build persistent learner context from stored application data.

    This is intentionally derived from existing collections instead of
    introducing a second memory database.
    """

    questions = await get_collection("questions").find({})

    reviews = await get_collection("reviews").find(
        {"user_id": user_id}
    )

    feynman_explanations = await get_collection(
        "feynman_explanations"
    ).find({})

    retention_by_topic = topic_retention(questions)
    weak_topics = weakest_topics(questions)
    due = due_counts(questions)

    # Most recent review events first.
    reviews_sorted = sorted(
        reviews,
        key=lambda review: review.get("reviewed_at"),
        reverse=True,
    )

    recent_reviews = [
        {
            "question_id": review.get("question_id"),
            "rating": review.get("rating"),
            "reviewed_at": review.get("reviewed_at"),
        }
        for review in reviews_sorted[:10]
    ]

    # Extract concepts that the student's Feynman checks identified
    # as missing.
    feynman_gaps: list[str] = []

    for explanation in feynman_explanations:
        check_result = explanation.get("check_result") or {}

        for gap in check_result.get("missing", []):
            if gap not in feynman_gaps:
                feynman_gaps.append(gap)

    return {
        "retention_by_topic": retention_by_topic,
        "weak_topics": weak_topics,
        "due_questions": (
            due["overdue"]
            + due["due_today"]
        ),
        "due_breakdown": due,
        "recent_reviews": recent_reviews,
        "feynman_gaps": feynman_gaps,
    }