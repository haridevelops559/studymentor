"""
State.

Concept being explored: LangGraph's core idea is a typed State object that
flows through every node -- each node receives the current state and returns
a partial update, which LangGraph merges in.

The state now supports both:
- adaptive learning decisions
- question generation / critique / retry
"""
from __future__ import annotations

from typing import Annotated, TypedDict

import operator


class QuestionGenState(TypedDict):
    # ------------------------------------------------------------------
    # Learning context
    # ------------------------------------------------------------------

    topic: str
    notes: str

    # Data supplied to the adaptive planner.
    # These are intentionally plain dictionaries so the graph can receive
    # data from the existing analytics/database layer without coupling the
    # graph state to database models.
    learning_state: dict

    # Decision produced by the adaptive planner.
    selected_activity: str
    selected_topic: str
    selected_difficulty: float
    decision_reason: str

    # ------------------------------------------------------------------
    # Agent execution
    # ------------------------------------------------------------------

    attempt_log: Annotated[list[str], operator.add]

    draft_questions: list[dict]

    # Result produced by Feynman/elaboration activities can be stored here
    # later without changing the graph state shape again.
    activity_result: dict

    # ------------------------------------------------------------------
    # Critique / retry
    # ------------------------------------------------------------------

    critique: str
    is_approved: bool
    retry_count: int

    # Set when automatic retries have been exhausted and human review
    # is required.
    needs_human_review: bool