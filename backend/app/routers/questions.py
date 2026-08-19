from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import get_collection
from app.schemas.question import Question, QuestionCreate
from app.services.scheduler import is_due

router = APIRouter(prefix="/questions", tags=["questions"])


@router.get("", response_model=list[Question])
async def list_questions(topic_id: str | None = None):
    query = {"topic_id": topic_id} if topic_id else {}
    return await get_collection("questions").find(query)


@router.post("", response_model=Question, status_code=201)
async def create_question(payload: QuestionCreate):
    doc = payload.model_dump()
    doc["next_review"] = datetime.now(timezone.utc)
    doc["review_count"] = 0
    doc["correct_count"] = 0
    doc["difficulty"] = 2.5
    created = await get_collection("questions").insert_one(doc)
    return created


@router.get("/due", response_model=list[Question])
async def due_questions(topic_id: str | None = None):
    query = {"topic_id": topic_id} if topic_id else {}
    all_questions = await get_collection("questions").find(query)
    now = datetime.now(timezone.utc)
    return [q for q in all_questions if is_due(q["next_review"], now)]


@router.get("/{question_id}", response_model=Question)
async def get_question(question_id: str):
    doc = await get_collection("questions").find_one({"_id": question_id})
    if doc is None:
        raise HTTPException(status_code=404, detail="Question not found")
    return doc
