import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_collection
from app.main import app


@pytest.mark.asyncio
async def test_create_question_persists_timestamps_and_is_due():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        subject = await client.post(
            "/api/subjects",
            json={"name": "Operating Systems"},
        )
        assert subject.status_code == 201
        subject_id = subject.json()["_id"]

        topic = await client.post(
            f"/api/subjects/{subject_id}/topics",
            json={
                "subject_id": subject_id,
                "name": "Virtual Memory",
            },
        )
        assert topic.status_code == 201
        topic_id = topic.json()["_id"]

        response = await client.post(
            "/api/questions",
            json={
                "topic_id": topic_id,
                "question": "What is virtual memory?",
                "answer": "A memory-management technique.",
                "type": "recall",
            },
        )

        assert response.status_code == 201

        question = response.json()

        assert question["created_at"] == question["next_review"]
        assert question["review_count"] == 0
        assert question["correct_count"] == 0
        assert question["difficulty"] == 2.5

        stored = await get_collection("questions").find_one(
            {"_id": question["_id"]}
        )

        assert stored is not None
        assert "created_at" in stored
        assert "next_review" in stored
        assert stored["created_at"] == stored["next_review"]

        due = await client.get("/api/questions/due")

        assert due.status_code == 200
        assert any(
            item["_id"] == question["_id"]
            for item in due.json()
        )