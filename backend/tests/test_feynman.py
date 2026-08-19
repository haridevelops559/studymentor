import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_collection
from app.main import app


@pytest.mark.asyncio
async def test_submit_feynman_persists_timestamp_and_check_result():
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
            "/api/feynman",
            json={
                "topic_id": topic_id,
                "explanation": (
                    "Virtual memory provides a memory abstraction "
                    "over physical memory."
                ),
                "checklist": [
                    "memory abstraction",
                    "physical memory",
                ],
            },
        )

        assert response.status_code == 201

        explanation = response.json()

        assert explanation["created_at"]
        assert explanation["check_result"]["coverage_ratio"] == 1.0
        assert explanation["check_result"]["missing"] == []
        assert set(explanation["check_result"]["covered"]) == {
            "memory abstraction",
            "physical memory",
        }

        stored = await get_collection(
            "feynman_explanations"
        ).find_one({"_id": explanation["_id"]})

        assert stored is not None
        assert "created_at" in stored
        assert stored["check_result"]["coverage_ratio"] == 1.0
        assert stored["check_result"]["missing"] == []