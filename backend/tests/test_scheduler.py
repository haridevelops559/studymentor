from datetime import datetime, timezone

from app.schemas.review import ReviewRating
from app.services.scheduler import is_due, next_review_date, update_difficulty


def test_again_reschedules_for_tomorrow():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    result = next_review_date(ReviewRating.again, review_count=5, difficulty=2.5, now=now)
    assert (result - now).days == 1


def test_easy_gives_longer_interval_than_hard():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    hard = next_review_date(ReviewRating.hard, review_count=0, difficulty=2.5, now=now)
    easy = next_review_date(ReviewRating.easy, review_count=0, difficulty=2.5, now=now)
    assert easy > hard


def test_graduated_interval_scales_with_ease_factor():
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    low_ease = next_review_date(ReviewRating.good, review_count=5, difficulty=1.5, now=now)
    high_ease = next_review_date(ReviewRating.good, review_count=5, difficulty=3.0, now=now)
    assert high_ease > low_ease


def test_ease_factor_clamped_within_bounds():
    difficulty = 1.3
    for _ in range(20):
        difficulty = update_difficulty(difficulty, ReviewRating.again)
    assert difficulty >= 1.3

    difficulty = 3.5
    for _ in range(20):
        difficulty = update_difficulty(difficulty, ReviewRating.easy)
    assert difficulty <= 3.5


def test_is_due():
    now = datetime(2026, 1, 10, tzinfo=timezone.utc)
    past = datetime(2026, 1, 9, tzinfo=timezone.utc)
    future = datetime(2026, 1, 11, tzinfo=timezone.utc)
    assert is_due(past, now) is True
    assert is_due(future, now) is False
