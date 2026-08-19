"""
Aggregation helpers that turn raw questions/reviews into the numbers the
dashboard shows (retention per topic, today's due counts, etc).

These operate on plain dicts (as returned by the database layer) rather than
Pydantic models, since they're aggregation logic, not I/O boundaries.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any


def topic_retention(questions: list[dict[str, Any]]) -> dict[str, float]:
    """
    Retention % per topic_id, based on each question's own correct/review
    ratio, averaged across the topic's questions.
    """
    by_topic: dict[str, list[float]] = defaultdict(list)

    for q in questions:
        review_count = q.get("review_count", 0)
        correct_count = q.get("correct_count", 0)
        if review_count == 0:
            continue
        by_topic[q["topic_id"]].append(100 * correct_count / review_count)

    return {
        topic_id: round(sum(ratios) / len(ratios), 1)
        for topic_id, ratios in by_topic.items()
    }


def due_counts(
    questions: list[dict[str, Any]], now: datetime | None = None
) -> dict[str, int]:
    """Bucket questions into overdue / due today / upcoming."""
    now = now or datetime.now(timezone.utc)
    today_end = now.replace(hour=23, minute=59, second=59, microsecond=0)

    overdue = due_today = upcoming = 0
    for q in questions:
        next_review = q.get("next_review")
        if next_review is None:
            continue
        if isinstance(next_review, str):
            next_review = datetime.fromisoformat(next_review)
        if next_review < now:
            overdue += 1
        elif next_review <= today_end:
            due_today += 1
        else:
            upcoming += 1

    return {"overdue": overdue, "due_today": due_today, "upcoming": upcoming}


def weakest_topics(
    questions: list[dict[str, Any]], limit: int = 3
) -> list[dict[str, Any]]:
    """
    Topics most worth reviewing: lowest retention among topics that have
    actually been reviewed at least once.
    """
    retention = topic_retention(questions)
    ranked = sorted(retention.items(), key=lambda kv: kv[1])
    return [
        {"topic_id": topic_id, "retention": pct} for topic_id, pct in ranked[:limit]
    ]
