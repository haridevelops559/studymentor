"""
Edges, Conditional routing, Retry loops, Checkpointing, Human approval,
Parallel branches, Subgraphs.

Concept being explored: this file wires app/agents/graph/nodes.py into an
actual StateGraph -- the "flowchart" that LangGraph executes.

    generate --> critique --(approved)--> END
                     |
                     (not approved, retries left)
                     v
              increment_retry --> generate   [retry loop]
                     |
                     (not approved, retries exhausted)
                     v
              human_approval --> END

Concepts demonstrated:
  - Nodes/Edges  : add_node / add_edge wire the graph above.
  - Conditional routing : `route_after_critique` picks the next node based
    on state, instead of a fixed edge.
  - Retry loop   : the edge back from increment_retry to generate, bounded
    by `retry_count` so it can't loop forever.
  - Checkpointing: `MemorySaver` persists state after every node, so a run
    can be resumed by `thread_id` instead of starting over.
  - Human approval: `human_approval_node` is a real node in the graph, not
    a UI-only concept -- production LangGraph would pair this with
    `interrupt_before=["human_approval"]` to actually pause execution and
    wait for a person, which requires a checkpointer (see below) so state
    survives the pause.
  - Parallel branches: `build_parallel_demo_graph()` fans one entry point
    into two nodes that both run before a join node -- shown separately
    since it doesn't fit the retry-loop graph's shape.
  - Subgraphs: `question_gen_subgraph()` compiles the whole graph above
    into a single reusable unit that a *larger* graph could embed as one
    node -- e.g. a future "full study-session" graph could call this
    subgraph, then hand off to a scheduling graph, without either graph
    knowing the other's internals.

Run: python -m app.agents.graph.build_graph   (requires Ollama running locally)
"""
from __future__ import annotations

from typing import TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from app.agents.graph.nodes import (
    critique_node,
    generate_node,
    human_approval_node,
    increment_retry_node,
)
from app.agents.graph.state import QuestionGenState

MAX_RETRIES = 2


def route_after_critique(state: QuestionGenState) -> str:
    """Conditional routing: inspect state, return the name of the next node."""
    if state["is_approved"]:
        return "end"
    if state["retry_count"] >= MAX_RETRIES:
        return "human_approval"
    return "retry"


def build_question_gen_graph():
    graph = StateGraph(QuestionGenState)

    graph.add_node("generate", generate_node)
    graph.add_node("critique", critique_node)
    graph.add_node("increment_retry", increment_retry_node)
    graph.add_node("human_approval", human_approval_node)

    graph.set_entry_point("generate")
    graph.add_edge("generate", "critique")

    # Conditional edge: the graph itself has no idea whether it's "done"
    # until `route_after_critique` inspects state at runtime.
    graph.add_conditional_edges(
        "critique",
        route_after_critique,
        {"end": END, "retry": "increment_retry", "human_approval": "human_approval"},
    )

    # Retry loop: bounded by MAX_RETRIES via route_after_critique, so this
    # can never spin forever even though it's a literal cycle in the graph.
    graph.add_edge("increment_retry", "generate")
    graph.add_edge("human_approval", END)

    # Checkpointing: MemorySaver persists state after every node transition,
    # keyed by a thread_id you pass at invoke time. Swap for a Postgres/
    # SQLite checkpointer in production so a run survives a process
    # restart -- same "swap the backend, keep the interface" pattern as
    # app/database.py.
    checkpointer = MemorySaver()

    return graph.compile(checkpointer=checkpointer)


def question_gen_subgraph():
    """
    Subgraphs: the compiled graph above IS a Runnable, so it can be
    embedded as a single node inside a larger graph. This function exists
    to make that reuse explicit and named, rather than inlining
    `build_question_gen_graph()` wherever it's needed.
    """
    return build_question_gen_graph()


# --- Parallel branches (separate, minimal graph to keep this concept
# isolated and easy to read on its own) -----------------------------------


def _branch_a(state: dict) -> dict:
    return {"result_a": f"summary of: {state['notes'][:30]}..."}


def _branch_b(state: dict) -> dict:
    return {"result_b": len(state["notes"].split())}


def _join(state: dict) -> dict:
    return {"combined": f"{state['result_a']} ({state['result_b']} words)"}


class ParallelState(TypedDict, total=False):
    notes: str
    result_a: str
    result_b: int
    combined: str


def build_parallel_demo_graph():
    """Two nodes run off the same entry point before a join node runs --
    LangGraph executes any nodes whose dependencies are already satisfied
    on the same "step" concurrently, which is what happens here since
    branch_a and branch_b both only depend on the initial state."""
    graph = StateGraph(ParallelState)
    graph.add_node("branch_a", _branch_a)
    graph.add_node("branch_b", _branch_b)
    graph.add_node("join", _join)

    # Multiple edges from START let both branches run off the same initial
    # state on the same graph "step" -- this is the modern LangGraph way to
    # express a fan-out (set_entry_point only supports a single entry node).
    graph.add_edge(START, "branch_a")
    graph.add_edge(START, "branch_b")
    graph.add_edge("branch_a", "join")
    graph.add_edge("branch_b", "join")
    graph.add_edge("join", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_question_gen_graph()

    initial_state: QuestionGenState = {
        "topic": "Virtual Memory",
        "notes": "Virtual memory lets a process use more address space than "
        "physical RAM by mapping pages to disk.",
        "attempt_log": [],
        "draft_questions": [],
        "critique": "",
        "is_approved": False,
        "retry_count": 0,
        "needs_human_review": False,
    }

    # thread_id is what the checkpointer uses to persist/resume this run.
    config = {"configurable": {"thread_id": "demo-run-1"}}
    final_state = app.invoke(initial_state, config=config)

    print("Attempt log:")
    for line in final_state["attempt_log"]:
        print(" -", line)
    print("\nApproved:", final_state["is_approved"])
    print("Needed human review:", final_state["needs_human_review"])
    print("Final questions:", final_state["draft_questions"])
