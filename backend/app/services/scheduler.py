"""
Spaced-repetition scheduling.

Deliberately simple for the MVP (a fixed interval ladder rather than a full
SM-2 implementation), but isolated behind `next_review_date` /
`update_difficulty` so it can be swapped for a smarter algorithm later
without touching routers.

Distributed practice -- reviewing material at spaced intervals rather than
all at once -- has strong evidence for improving longer-term retention.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.schemas.review import ReviewRating

# rating -> (days until next review, ease-factor delta)
_INTERVAL_LADDER: dict[ReviewRating, tuple[int, float]] = {
    ReviewRating.again: (1, -0.3),
    ReviewRating.hard: (2, -0.15),
    ReviewRating.good: (4, 0.0),
    ReviewRating.easy: (7, 0.15),
}

# Once a question has been reviewed enough times successfully, intervals
# grow using the ease factor rather than the flat ladder above.
_GRADUATED_REVIEW_COUNT = 3
MIN_EASE = 1.3
MAX_EASE = 3.5


def next_review_date(
    rating: ReviewRating,
    review_count: int,
    difficulty: float,
    now: datetime | None = None,
) -> datetime:
    """Return the next review datetime for a question given a rating."""
    now = now or datetime.now(timezone.utc)
    base_days, _ = _INTERVAL_LADDER[rating]

    if review_count < _GRADUATED_REVIEW_COUNT or rating == ReviewRating.again:
        days = base_days
    else:
        # Graduated interval: previous interval scaled by ease factor.
        days = max(base_days, round(base_days * difficulty))

    return now + timedelta(days=days)


def update_difficulty(current_difficulty: float, rating: ReviewRating) -> float:
    """Adjust the ease factor for a question based on the latest rating."""
    _, delta = _INTERVAL_LADDER[rating]
    updated = current_difficulty + delta
    return max(MIN_EASE, min(MAX_EASE, round(updated, 2)))


def is_due(next_review: datetime, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    return next_review <= now
