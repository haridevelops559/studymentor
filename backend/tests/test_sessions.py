import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_session_start_and_finish_lifecycle():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        started = await client.post(
            "/api/sessions",
            json={
                "user_id": "demo-user",
                "planned_activities": [
                    "review questions",
                    "Feynman explanation",
                ],
            },
        )

        assert started.status_code == 201

        session = started.json()
        session_id = session["_id"]

        assert session["started_at"] is not None
        assert session["ended_at"] is None
        assert session["duration_seconds"] is None

        await asyncio.sleep(1.1)

        finished = await client.patch(
            f"/api/sessions/{session_id}/finish",
            json={
                "questions_attempted": 5,
                "questions_correct": 4,
                "topics_reviewed": ["topics_1"],
            },
        )

        assert finished.status_code == 200

        result = finished.json()

        assert result["ended_at"] is not None
        assert result["duration_seconds"] >= 1
        assert result["questions_attempted"] == 5
        assert result["questions_correct"] == 4
        assert result["topics_reviewed"] == ["topics_1"]


@pytest.mark.asyncio
async def test_finished_session_cannot_be_finished_again():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        started = await client.post(
            "/api/sessions",
            json={"user_id": "demo-user"},
        )

        assert started.status_code == 201

        session_id = started.json()["_id"]

        finished = await client.patch(
            f"/api/sessions/{session_id}/finish",
            json={
                "questions_attempted": 5,
                "questions_correct": 4,
                "topics_reviewed": ["topics_1"],
            },
        )

        assert finished.status_code == 200

        finished_again = await client.patch(
            f"/api/sessions/{session_id}/finish",
            json={
                "questions_attempted": 10,
                "questions_correct": 10,
                "topics_reviewed": ["topics_2"],
            },
        )

        assert finished_again.status_code == 400
        assert finished_again.json()["detail"] == "Session already finished"