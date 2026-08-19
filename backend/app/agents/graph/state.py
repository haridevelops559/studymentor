"""
State.

Concept being explored: LangGraph's core idea is a typed State object that
flows through every node in the graph -- each node receives the current
state and returns a partial update, which LangGraph merges in.

This State models one run of the "generate questions from notes, self-
critique them, retry if bad" workflow (see graph/build_graph.py for the
graph that operates on it).
"""
from __future__ import annotations

from typing import Annotated, TypedDict

import operator


class QuestionGenState(TypedDict):
    topic: str
    notes: str

    # Annotated with operator.add so LangGraph APPENDS to this list across
    # nodes/loop iterations instead of overwriting it -- this is how you
    # accumulate a retry history in LangGraph rather than losing it each
    # time a node returns.
    attempt_log: Annotated[list[str], operator.add]

    draft_questions: list[dict]
    critique: str
    is_approved: bool
    retry_count: int

    # Set only when the human-approval node is reached -- see
    # graph/build_graph.py's `human_approval_node` for how this is used
    # as a conditional-routing signal.
    needs_human_review: bool
