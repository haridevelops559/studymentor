from fastapi import APIRouter, HTTPException

from app.database import get_collection
from app.schemas.subject import Subject, SubjectCreate, Topic, TopicCreate

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.get("", response_model=list[Subject])
async def list_subjects():
    docs = await get_collection("subjects").find({})
    return docs


@router.post("", response_model=Subject, status_code=201)
async def create_subject(payload: SubjectCreate):
    doc = await get_collection("subjects").insert_one(payload.model_dump())
    return doc


@router.get("/{subject_id}/topics", response_model=list[Topic])
async def list_topics(subject_id: str):
    return await get_collection("topics").find({"subject_id": subject_id})


@router.post("/{subject_id}/topics", response_model=Topic, status_code=201)
async def create_topic(subject_id: str, payload: TopicCreate):
    subject = await get_collection("subjects").find_one({"_id": subject_id})
    if subject is None:
        raise HTTPException(status_code=404, detail="Subject not found")
    if payload.subject_id != subject_id:
        raise HTTPException(status_code=400, detail="subject_id mismatch")
    doc = await get_collection("topics").insert_one(payload.model_dump())
    return doc
