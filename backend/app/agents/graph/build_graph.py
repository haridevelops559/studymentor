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
import asyncio
from typing import TypedDict
from app.agents.graph.nodes import (
    adaptive_planner_node,
    critique_node,
    elaboration_node,
    feynman_node,
    generate_node,
    human_approval_node,
    increment_retry_node,
    load_memory_node,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph


from app.agents.graph.state import QuestionGenState

MAX_RETRIES = 2


def route_after_critique(state: QuestionGenState) -> str:
    """Conditional routing: inspect state, return the name of the next node."""
    if state["is_approved"]:
        return "end"
    if state["retry_count"] >= MAX_RETRIES:
        return "human_approval"
    return "retry"

def route_after_planner(state: QuestionGenState) -> str:
    """Route to the learning activity selected by the adaptive planner."""

    activity = state["selected_activity"]

    if activity == "feynman":
        return "feynman"

    if activity == "retrieval":
        return "retrieval"

    if activity == "elaboration":
        return "elaboration"

    return "end"



def build_question_gen_graph():
    graph = StateGraph(QuestionGenState)

    # -------------------------
    # Nodes
    # -------------------------
    graph.add_node(
         "load_memory",
          load_memory_node,
    )
    graph.add_node(
        "adaptive_planner",
        adaptive_planner_node,
    )

    graph.add_node(
        "generate",
        generate_node,
    )

    graph.add_node(
        "feynman",
        feynman_node,
    )
    graph.add_node(
        "elaboration",
         elaboration_node,
    )

    graph.add_node(
        "quality_check",
        critique_node,
    )

    graph.add_node(
        "increment_retry",
        increment_retry_node,
    )

    graph.add_node(
        "human_approval",
        human_approval_node,
    )

    # -------------------------
    # Entry
    # -------------------------

    graph.set_entry_point("load_memory")
    graph.add_edge("load_memory", "adaptive_planner")

    # -------------------------
    # Planner → activity
    # -------------------------

    graph.add_conditional_edges(
        "adaptive_planner",
        route_after_planner,
        {
            "retrieval": "generate",
            "feynman": "feynman",
            "elaboration": "elaboration" ,
            "end": END,
        },
    )
    graph.add_edge(
        "elaboration",
         END,
    )

    # -------------------------
    # Retrieval branch
    # -------------------------

    graph.add_edge(
        "generate",
        "quality_check",
    )

    graph.add_conditional_edges(
        "quality_check",
        route_after_critique,
        {
            "end": END,
            "retry": "increment_retry",
            "human_approval": "human_approval",
        },
    )

    graph.add_edge(
        "increment_retry",
        "generate",
    )

    # -------------------------
    # Feynman branch
    # -------------------------

    graph.add_edge(
        "feynman",
        END,
    )

    # -------------------------
    # Human review
    # -------------------------

    graph.add_edge(
        "human_approval",
        END,
    )

    # -------------------------
    # Checkpointing
    # -------------------------

    checkpointer = MemorySaver()

    return graph.compile(
        checkpointer=checkpointer,
    )
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


async def main():
    app = build_question_gen_graph()

    initial_state: QuestionGenState = {
        "user_id": "demo-user",
        "topic": "Virtual Memory",
        "notes": (
            "Virtual memory lets a process use more address space than "
            "physical RAM by mapping pages to disk. Page faults occur "
            "when a needed page is not in physical memory."
        ),
        "learning_state": {
            "weak_topics": [
                {
                    "topic_id": "Virtual Memory",
                    "retention": 52.0,
                }
            ],
            "due_questions": 4,
            "recent_reviews": [
                {"rating": "again"},
                {"rating": "hard"},
                {"rating": "again"},
            ],
            "feynman_gaps": [
                "page fault",
            ],
        },
        "selected_activity": "",
        "selected_topic": "",
        "selected_difficulty": 2.0,
        "decision_reason": "",
        "attempt_log": [],
        "draft_questions": [],
        "activity_result": {},
        "critique": "",
        "is_approved": False,
        "retry_count": 0,
        "needs_human_review": False,
    }

    # thread_id allows LangGraph's checkpointer to identify and resume
    # this particular workflow execution.
    config = {
        "configurable": {
            "thread_id": "demo-adaptive-run-1"
        }
    }

    final_state = await app.ainvoke(
        initial_state,
        config=config,
    )

    print("\n=== ADAPTIVE LEARNING DECISION ===")
    print("Activity:", final_state["selected_activity"])
    print("Topic:", final_state["selected_topic"])
    print("Difficulty:", final_state["selected_difficulty"])
    print("Reason:", final_state["decision_reason"])

    print("\n=== AGENT ATTEMPT LOG ===")
    for line in final_state["attempt_log"]:
        print(" -", line)

    print("\n=== CRITIQUE ===")
    print(final_state["critique"])

    print("\n=== FINAL STATUS ===")
    print("Approved:", final_state["is_approved"])
    print("Retries used:", final_state["retry_count"])
    print("Needs human review:", final_state["needs_human_review"])

    print("\n=== ACTIVITY RESULT ===")
    print(final_state["activity_result"])

    print("\n=== FINAL QUESTIONS ===")
    for index, question in enumerate(
        final_state["draft_questions"],
        start=1,
    ):
        print(f"\n{index}. {question['question']}")
        print(f"   Answer: {question['answer']}")

if __name__ == "__main__":
    asyncio.run(main())