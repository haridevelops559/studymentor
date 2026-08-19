import asyncio

import pytest
from httpx import ASGITransport, AsyncClient

from app.database import get_collection
from app.main import app


@pytest.mark.asyncio
async def test_note_timestamps_follow_create_update_lifecycle():
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

        created = await client.post(
            "/api/notes",
            json={
                "topic_id": topic_id,
                "title": "Virtual Memory",
                "content": (
                    "Virtual memory provides an abstraction "
                    "of physical memory."
                ),
                "cues": ["paging", "page table"],
                "summary": "Memory abstraction using secondary storage.",
            },
        )

        assert created.status_code == 201
        note = created.json()

        created_at = note["created_at"]
        updated_at = note["updated_at"]

        # On creation, both timestamps should be identical.
        assert created_at == updated_at

        # Ensure the update timestamp is observably later.
        await asyncio.sleep(0.01)

        updated = await client.patch(
            f"/api/notes/{note['_id']}",
            json={"title": "Virtual Memory - Updated"},
        )

        assert updated.status_code == 200
        updated_note = updated.json()

        # created_at must remain unchanged.
        assert updated_note["created_at"] == created_at

        # updated_at must change after the update.
        assert updated_note["updated_at"] != updated_at

        stored = await get_collection("notes").find_one(
            {"_id": note["_id"]}
        )

        assert stored is not None

        # The database stores datetime objects while the API returns
        # ISO-8601 strings, so normalize the database values before comparing.
        assert (
            stored["created_at"].isoformat().replace("+00:00", "Z")
            == updated_note["created_at"]
        )
        assert (
            stored["updated_at"].isoformat().replace("+00:00", "Z")
            == updated_note["updated_at"]
        )