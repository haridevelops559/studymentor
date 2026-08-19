"""
LangGraph nodes for StudyMentor.

The graph contains:
- adaptive planning
- retrieval practice
- Feynman self-explanation
- deterministic quality checking
- bounded retries
- human review
"""
from __future__ import annotations

from app.agents.chains import (
    build_feynman_feedback_chain,
    build_learning_decision_chain,
    build_question_generation_chain,
)
from app.agents.graph.state import QuestionGenState
from app.services.scoring import check_feynman_coverage


def adaptive_planner_node(state: QuestionGenState) -> dict:
    """Choose the learning activity for the current learner state."""
    chain = build_learning_decision_chain()

    decision = chain.invoke(
        {
            "learning_state": str(state["learning_state"]),
        }
    )

    return {
        "selected_activity": decision.activity,
        "selected_topic": decision.topic,
        "selected_difficulty": decision.difficulty,
        "decision_reason": decision.reason,
        "attempt_log": [
            (
                f"[planner] selected '{decision.activity}' for "
                f"'{decision.topic}' at difficulty "
                f"{decision.difficulty}: {decision.reason}"
            )
        ],
    }


def generate_node(state: QuestionGenState) -> dict:
    """
    Retrieval-practice executor.

    Generates questions from the selected topic's notes.
    """
    chain = build_question_generation_chain()

    topic = state["selected_topic"] or state["topic"]

    result = chain.invoke(
        {
            "topic": topic,
            "notes": state["notes"],
            "num_questions": 3,
        }
    )

    questions = [q.model_dump() for q in result.questions]

    return {
        "draft_questions": questions,
        "activity_result": {
            "activity": "retrieval",
            "topic": topic,
            "question_count": len(questions),
        },
        "attempt_log": [
            f"[retrieval] generated {len(questions)} questions for '{topic}'"
        ],
    }


def feynman_node(state: QuestionGenState) -> dict:
    """
    Feynman self-explanation executor.

    The learner's explanation is checked deterministically against the
    supplied checklist. If an LLM feedback chain is available, it can then
    turn the missing concepts into concise coaching feedback.
    """
    topic = state["selected_topic"] or state["topic"]

    learning_state = state["learning_state"]

    explanation = learning_state.get("feynman_explanation", "")

    checklist = learning_state.get("feynman_checklist", [])

    if not explanation:
        return {
            "activity_result": {
                "activity": "feynman",
                "topic": topic,
                "status": "awaiting_explanation",
                "check_result": None,
            },
            "attempt_log": [
                (
                    f"[feynman] waiting for student explanation "
                    f"for '{topic}'"
                )
            ],
        }

    if not checklist:
        return {
            "activity_result": {
                "activity": "feynman",
                "topic": topic,
                "status": "missing_checklist",
                "check_result": None,
            },
            "attempt_log": [
                (
                    f"[feynman] no checklist supplied for "
                    f"'{topic}'"
                )
            ],
        }

    check_result = check_feynman_coverage(
        explanation,
        checklist,
    )

    feedback = ""

    # Optional LLM feedback. The deterministic checker remains the source
    # of truth for coverage.
    try:
        feedback_chain = build_feynman_feedback_chain()

        feedback_result = feedback_chain.invoke(
            {
                "topic": topic,
                "explanation": explanation,
                "checklist": checklist,
            }
        )

        feedback = str(feedback_result).strip()

    except Exception as exc:
        # Feynman scoring still works if the local LLM is unavailable.
        feedback = (
            "Review the missing concepts: "
            + ", ".join(check_result.missing)
            if check_result.missing
            else "Your explanation covered the supplied concepts."
        )

        print(f"[feynman] optional LLM feedback unavailable: {exc}")

    result = check_result.model_dump()

    return {
        "activity_result": {
            "activity": "feynman",
            "topic": topic,
            "status": "completed",
            "check_result": result,
            "feedback": feedback,
        },
        "attempt_log": [
            (
                f"[feynman] coverage={check_result.coverage_ratio}, "
                f"covered={len(check_result.covered)}, "
                f"missing={len(check_result.missing)}"
            )
        ],
    }


def critique_node(state: QuestionGenState) -> dict:
    """
    Deterministic quality check for retrieval-generated questions.
    """
    questions = state["draft_questions"]

    weak = [
        q
        for q in questions
        if len(q["answer"].split()) < 3
    ]

    if weak:
        critique = (
            f"{len(weak)} question(s) have answers that are too short."
        )
        approved = False
    else:
        critique = "All questions meet the minimum answer-quality bar."
        approved = True

    return {
        "critique": critique,
        "is_approved": approved,
        "attempt_log": [
            f"[critic] {critique}"
        ],
    }


def increment_retry_node(state: QuestionGenState) -> dict:
    """Increment the bounded retry counter."""
    return {
        "retry_count": state["retry_count"] + 1,
    }


def human_approval_node(state: QuestionGenState) -> dict:
    """
    Flag the workflow for human review after automatic retries are
    exhausted.
    """
    return {
        "needs_human_review": True,
        "attempt_log": [
            (
                "[human-review] automatic retries exhausted; "
                "human review required"
            )
        ],
    }