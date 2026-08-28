"""
Agent API boundary for StudyMentor.

The frontend talks to this router without knowing about LangChain,
LangGraph, Ollama, or learner-memory implementation details.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(
    prefix="/agents",
    tags=["agents"],
)


# ---------------------------------------------------------------------------
# Existing question-generation API
# ---------------------------------------------------------------------------

class GenerateQuestionsRequest(BaseModel):
    topic: str
    notes: str
    num_questions: int = 3


class GeneratedQuestionOut(BaseModel):
    question: str
    answer: str


class GenerateQuestionsResponse(BaseModel):
    questions: list[GeneratedQuestionOut]


# ---------------------------------------------------------------------------
# Adaptive-agent API
# ---------------------------------------------------------------------------

class AgentRecommendationResponse(BaseModel):
    activity: str
    topic: str
    difficulty: float
    reason: str

    retention: float | None = None
    due_questions: int = 0
    feynman_gaps: list[str] = []
    attempt_log: list[str] = []


def _agents_available() -> bool:
    try:
        import langchain_core  # noqa: F401
        import langchain_ollama  # noqa: F401
        import langgraph  # noqa: F401
    except ImportError:
        return False

    return True


@router.post(
    "/recommendation",
    response_model=AgentRecommendationResponse,
)
async def get_agent_recommendation(
    user_id: str = "demo-user",
):
    """
    Run the adaptive LangGraph workflow and expose the planner's
    learning-activity decision to the frontend.

    The decision is based on learner memory rather than a frontend
    hard-coded rule.
    """

    if not _agents_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Agent layer is not available. Install the agent "
                "dependencies from requirements-agents.txt."
            ),
        )

    from app.agents.graph.build_graph import build_question_gen_graph
    from app.agents.memory.learner_memory import build_learner_memory

    try:
        learning_state = await build_learner_memory(user_id)

        # Use the learner's weakest topic as the initial context.
        # The planner itself still makes the activity decision.
        weak_topics = learning_state.get("weak_topics", [])

        if weak_topics:
            initial_topic = weak_topics[0]["topic_id"]
        else:
            initial_topic = "General Review"

        initial_state = {
            "user_id": user_id,
            "topic": initial_topic,
            "notes": "",
            "learning_state": {},

            "selected_activity": "",
            "selected_topic": "",
            "selected_difficulty": 0.0,
            "decision_reason": "",

            "attempt_log": [],
            "draft_questions": [],
            "activity_result": {},

            "critique": "",
            "is_approved": False,
            "retry_count": 0,
            "needs_human_review": False,
        }

        graph = build_question_gen_graph()

        final_state = await graph.ainvoke(
            initial_state,
            config={
                "configurable": {
                    "thread_id": f"recommendation-{user_id}",
                }
            },
        )

    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=f"Adaptive agent execution failed: {exc}",
        ) from exc

    retention = learning_state.get(
        "retention_by_topic",
        {},
    ).get(
        final_state["selected_topic"],
    )

    return AgentRecommendationResponse(
        activity=final_state["selected_activity"],
        topic=final_state["selected_topic"],
        difficulty=final_state["selected_difficulty"],
        reason=final_state["decision_reason"],
        retention=retention,
        due_questions=learning_state.get("due_questions", 0),
        feynman_gaps=learning_state.get("feynman_gaps", []),
        attempt_log=final_state.get("attempt_log", []),
    )


# ---------------------------------------------------------------------------
# Existing question-generation endpoint
# ---------------------------------------------------------------------------

@router.post(
    "/generate-questions",
    response_model=GenerateQuestionsResponse,
)
async def generate_questions(
    payload: GenerateQuestionsRequest,
):
    """
    Generate structured retrieval questions using the LLM layer.
    """

    if not _agents_available():
        raise HTTPException(
            status_code=503,
            detail=(
                "Agent layer not installed. Run: "
                "pip install -r requirements-agents.txt"
            ),
        )

    from app.agents.chains import build_question_generation_chain

    try:
        chain = build_question_generation_chain()

        result = await chain.ainvoke(
            {
                "topic": payload.topic,
                "notes": payload.notes,
                "num_questions": payload.num_questions,
            }
        )

    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=502,
            detail=(
                f"Could not reach local Ollama or parse its response: {exc}"
            ),
        ) from exc

    return GenerateQuestionsResponse(
        questions=[
            GeneratedQuestionOut(
                question=q.question,
                answer=q.answer,
            )
            for q in result.questions
        ]
    )