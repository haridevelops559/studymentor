from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone
from app.database import get_collection
from app.schemas.note import Note, NoteCreate, NoteUpdate

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("", response_model=list[Note])
async def list_notes(topic_id: str | None = None):
    query = {"topic_id": topic_id} if topic_id else {}
    return await get_collection("notes").find(query)


@router.post("", response_model=Note, status_code=201)
async def create_note(payload: NoteCreate):
    doc = payload.model_dump()
    now = datetime.now(timezone.utc)
    doc["created_at"] = now
    doc["updated_at"] = now

    created = await get_collection("notes").insert_one(doc)
    return created


@router.patch("/{note_id}", response_model=Note)
async def update_note(note_id: str, payload: NoteUpdate):
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    updates["updated_at"] = datetime.now(timezone.utc)
    doc = await get_collection("notes").update_one(
        {"_id": note_id},
        updates,
    )
    if doc is None:
        raise HTTPException(status_code=404, detail="Note not found")
    return doc
