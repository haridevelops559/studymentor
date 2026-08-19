import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_full_review_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        subject = await client.post(
            "/api/subjects", json={"name": "Operating Systems"}
        )
        assert subject.status_code == 201
        subject_id = subject.json()["_id"]

        topic = await client.post(
            f"/api/subjects/{subject_id}/topics",
            json={"subject_id": subject_id, "name": "Virtual Memory"},
        )
        assert topic.status_code == 201
        topic_id = topic.json()["_id"]

        question = await client.post(
            "/api/questions",
            json={
                "topic_id": topic_id,
                "question": "What problem does virtual memory solve?",
                "answer": "Lets a process use more address space than physical RAM.",
            },
        )
        assert question.status_code == 201
        question_id = question.json()["_id"]

        due = await client.get("/api/questions/due")
        assert any(q["_id"] == question_id for q in due.json())

        review = await client.post(
            "/api/reviews",
            json={"question_id": question_id, "rating": "good", "given_answer": "..."},
        )
        assert review.status_code == 201
        assert review.json()["next_review"] > review.json()["reviewed_at"]

        updated_question = await client.get(f"/api/questions/{question_id}")
        assert updated_question.json()["review_count"] == 1
        assert updated_question.json()["correct_count"] == 1


@pytest.mark.asyncio
async def test_review_for_missing_question_returns_404():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/reviews",
            json={"question_id": "does-not-exist", "rating": "good"},
        )
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_dashboard_endpoint_returns_shape():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/dashboard")
        assert response.status_code == 200
        body = response.json()
        for key in ["due", "retention_by_topic", "weakest_topics"]:
            assert key in body
