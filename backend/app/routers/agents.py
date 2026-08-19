"""
Wires app/agents/ into the API as one optional router.

This is "the layer" the rest of the app talks to -- everything upstream
(main.py, the frontend) only knows about this endpoint's request/response
shape, never about LangChain/LangGraph/Ollama directly. That's the same
adapter principle used for storage (app/database.py) and the LLM client
(app/agents/llm.py) applied one level up, at the API boundary.

Deliberately import-guarded: if langchain/langgraph aren't installed (the
default -- see requirements-agents.txt), this router still loads and
returns a clear 503 instead of crashing the whole API at startup. This
mirrors how a real production system should degrade a non-critical,
experimental feature rather than let it take down the core product.
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/agents", tags=["agents (experimental)"])


class GenerateQuestionsRequest(BaseModel):
    topic: str
    notes: str
    num_questions: int = 3


class GeneratedQuestionOut(BaseModel):
    question: str
    answer: str


class GenerateQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestionOut]


def _agents_available() -> bool:
    try:
        import langchain_core  # noqa: F401
        import langchain_ollama  # noqa: F401
    except ImportError:
        return False
    return True


@router.post("/generate-questions", response_model=GenerateQuestionsResponse)
async def generate_questions(payload: GenerateQuestionsRequest):
    """
    LLM-assisted question generation -- the exact 'AI-generated questions'
    feature explicitly scoped OUT of the core MVP (see README.md roadmap).
    It lives behind this separate, optional router precisely so it can be
    demoed/graded independently without becoming a hard dependency of the
    tested core product.
    """
    if not _agents_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Agent layer not installed. Run: "
                "pip install -r requirements-agents.txt, then ensure "
                "`ollama serve` is running locally. See "
                "docs/AGENT-LAYER-GUIDE.md."
            ),
        )

    from app.agents.chains import build_question_generation_chain

    try:
        chain = build_question_generation_chain()
        result = chain.invoke(
            {
                "topic": payload.topic,
                "notes": payload.notes,
                "num_questions": payload.num_questions,
            }
        )
    except Exception as exc:  # noqa: BLE001 -- surfaced to the client below
        raise HTTPException(
            status_code=502,
            detail=f"Could not reach local Ollama or parse its response: {exc}",
        ) from exc

    return GenerateQuestionsResponse(
        questions=[
            GeneratedQuestionOut(question=q.question, answer=q.answer)
            for q in result.questions
        ]
    )
