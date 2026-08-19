from datetime import datetime, timedelta, timezone

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_collection
from app.main import app


@pytest.mark.asyncio
async def test_dashboard_counts_only_sessions_ended_today():
    now = datetime.now(timezone.utc)

    sessions = get_collection("study_sessions")

    await sessions.insert_one(
        {
            "user_id": "demo-user",
            "started_at": now - timedelta(days=2, minutes=30),
            "ended_at": now - timedelta(days=2),
            "duration_seconds": 1800,
            "questions_attempted": 10,
            "questions_correct": 8,
            "topics_reviewed": ["old-topic"],
        }
    )

    await sessions.insert_one(
        {
            "user_id": "demo-user",
            "started_at": now - timedelta(minutes=30),
            "ended_at": now,
            "duration_seconds": 1800,
            "questions_attempted": 5,
            "questions_correct": 4,
            "topics_reviewed": ["today-topic"],
        }
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.get("/api/dashboard")

    assert response.status_code == 200

    dashboard = response.json()

    assert dashboard["minutes_studied_today"] == 30
    assert dashboard["reviews_completed_today"] == 5
    assert dashboard["recall_percent_today"] == 80.0
    assert dashboard["topics_touched_today"] == 1