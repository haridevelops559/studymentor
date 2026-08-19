from fastapi import APIRouter
from datetime import datetime, timezone
from app.database import get_collection
from app.schemas.feynman import FeynmanCreate, FeynmanExplanation
from app.services.scoring import check_feynman_coverage

router = APIRouter(prefix="/feynman", tags=["feynman"])


@router.get("/{topic_id}", response_model=list[FeynmanExplanation])
async def list_explanations(topic_id: str):
    return await get_collection("feynman_explanations").find({"topic_id": topic_id})


@router.post("", response_model=FeynmanExplanation, status_code=201)
async def submit_explanation(payload: FeynmanCreate):
    check_result = check_feynman_coverage(payload.explanation, payload.checklist)
    doc = payload.model_dump()
    doc["created_at"] = datetime.now(timezone.utc)
    doc["check_result"] = check_result.model_dump()
    created = await get_collection("feynman_explanations").insert_one(doc)
    return created
