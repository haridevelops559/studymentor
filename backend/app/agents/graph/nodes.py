"""
Nodes.

Concept being explored: a LangGraph node is a function
`(state) -> partial_state_update`.

The graph now contains an adaptive planner that chooses a learning
intervention before the existing question-generation workflow runs.

Flow:

    adaptive_planner
          ↓
    selected activity
          ↓
    generate
          ↓
      critique
          ↓
    retry / human / END
"""
from __future__ import annotations

from app.agents.chains import (
    build_learning_decision_chain,
    build_question_generation_chain,
)
from app.agents.graph.state import QuestionGenState


def adaptive_planner_node(state: QuestionGenState) -> dict:
    """
    Ask the adaptive learning planner to choose the most appropriate
    learning intervention from the student's current learning state.

    The LLM does NOT calculate retention or scheduling itself. Those values
    are supplied by the deterministic backend/analytics layer.
    """
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
                f"'{decision.topic}' at difficulty {decision.difficulty}: "
                f"{decision.reason}"
            )
        ],
    }


def generate_node(state: QuestionGenState) -> dict:
    """
    Generate (or regenerate) retrieval-practice questions.

    The planner has already selected the topic and activity. For the
    retrieval path, the existing question-generation chain is reused.
    """
    chain = build_question_generation_chain()

    topic = state["selected_topic"] or state["topic"]

    # The current state still carries the notes for the topic being
    # generated. A later version can retrieve notes dynamically based on
    # selected_topic.
    result = chain.invoke(
        {
            "topic": topic,
            "notes": state["notes"],
            "num_questions": 3,
        }
    )

    return {
        "draft_questions": [q.model_dump() for q in result.questions],
        "activity_result": {
            "activity": "retrieval",
            "topic": topic,
            "question_count": len(result.questions),
        },
        "attempt_log": [
            f"[retrieval] generated {len(result.questions)} questions for '{topic}'"
        ],
    }


def critique_node(state: QuestionGenState) -> dict:
    """
    Reflection/Critic step.

    This remains deterministic: generated questions are checked against
    an explicit quality rule rather than asking the LLM to grade itself.
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
        "attempt_log": [f"[critic] {critique}"],
    }


def increment_retry_node(state: QuestionGenState) -> dict:
    """Bookkeeping node for the bounded retry loop."""
    return {
        "retry_count": state["retry_count"] + 1,
    }


def human_approval_node(state: QuestionGenState) -> dict:
    """
    Human-in-the-loop checkpoint.

    If automatic retries are exhausted without meeting the quality bar,
    flag the run for human review instead of silently accepting weak output.
    """
    return {
        "needs_human_review": True,
        "attempt_log": [
            "[human-review] automatic retries exhausted; human review required"
        ],
    }