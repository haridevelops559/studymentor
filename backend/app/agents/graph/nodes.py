"""
Nodes.

Concept being explored: a LangGraph node is just a function
`(state) -> partial_state_update`. Nodes are where the actual work happens
-- calling an LLM, calling a tool, running pure Python logic. The graph
(build_graph.py) only wires nodes together; it contains no business logic
itself.
"""
from __future__ import annotations

from app.agents.chains import build_question_generation_chain
from app.agents.graph.state import QuestionGenState


def generate_node(state: QuestionGenState) -> dict:
    """Generate (or regenerate) questions from the notes."""
    chain = build_question_generation_chain()
    result = chain.invoke(
        {
            "topic": state["topic"],
            "notes": state["notes"],
            "num_questions": 3,
        }
    )
    return {
        "draft_questions": [q.model_dump() for q in result.questions],
        "attempt_log": [f"generated {len(result.questions)} questions"],
    }


def critique_node(state: QuestionGenState) -> dict:
    """
    Self-critique step (Reflection pattern): check the generated questions
    against a simple, deterministic rule rather than asking the LLM to
    grade itself, which is unreliable. Each question must have a non-empty
    answer at least 3 words long -- a stand-in for a real quality bar.
    """
    questions = state["draft_questions"]
    weak = [q for q in questions if len(q["answer"].split()) < 3]

    if weak:
        critique = f"{len(weak)} question(s) have answers that are too short."
        approved = False
    else:
        critique = "All questions meet the minimum answer-quality bar."
        approved = True

    return {
        "critique": critique,
        "is_approved": approved,
        "attempt_log": [f"critique: {critique}"],
    }


def increment_retry_node(state: QuestionGenState) -> dict:
    """Bookkeeping node for the retry loop -- see build_graph.py."""
    return {"retry_count": state["retry_count"] + 1}


def human_approval_node(state: QuestionGenState) -> dict:
    """
    Human-in-the-loop checkpoint: after retries are exhausted without
    passing the automatic critique, flag the run for a human to review
    rather than silently shipping low-quality questions. In a real
    deployment this would pause the graph (via LangGraph's
    `interrupt_before`) and wait for external input instead of just
    setting a flag -- see the note in build_graph.py.
    """
    return {"needs_human_review": True}
