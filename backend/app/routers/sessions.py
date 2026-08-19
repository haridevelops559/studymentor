from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_collection
from app.schemas.session import SessionFinish, SessionStart, StudySession

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=StudySession, status_code=201)
async def start_session(payload: SessionStart):
    doc = payload.model_dump()
    doc["started_at"] = datetime.now(timezone.utc)
    created = await get_collection("study_sessions").insert_one(doc)
    return created


@router.patch("/{session_id}/finish", response_model=StudySession)
async def finish_session(session_id: str, payload: SessionFinish):
    session = await get_collection("study_sessions").find_one({"_id": session_id})
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    ended_at = datetime.now(timezone.utc)
    started_at = session["started_at"]
    duration = int((ended_at - started_at).total_seconds())

    updates = payload.model_dump()
    updates["ended_at"] = ended_at
    updates["duration_seconds"] = duration

    doc = await get_collection("study_sessions").update_one(
        {"_id": session_id}, updates
    )
    return doc
