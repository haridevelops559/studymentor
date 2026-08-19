import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_collection
from app.main import app


@pytest.mark.asyncio
async def test_create_subject_persists_created_at():
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        response = await client.post(
            "/api/subjects",
            json={
                "name": "Operating Systems",
                "description": "Core OS concepts",
            },
        )

        assert response.status_code == 201

        body = response.json()

        assert "created_at" in body
        assert body["created_at"]

        stored = await get_collection("subjects").find_one(
            {"_id": body["_id"]}
        )

        assert stored is not None
        assert "created_at" in stored