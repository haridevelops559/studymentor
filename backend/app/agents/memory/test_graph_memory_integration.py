"""
End-to-end test:

seed persistent learner data
        ↓
LangGraph load_memory node
        ↓
adaptive planner
        ↓
selected learning activity

This verifies that persistent learner memory actually influences
the LangGraph decision.
"""

from __future__ import annotations

import asyncio

from app.agents.graph.build_graph import build_question_gen_graph
from app.agents.memory.seed_memory_demo import seed


USER_ID = "demo-user"


async def main():
    print("=" * 60)
    print("GRAPH + PERSISTENT MEMORY INTEGRATION TEST")
    print("=" * 60)

    # ---------------------------------------------------------------
    # 1. Seed learner history in the SAME Python process.
    # ---------------------------------------------------------------

    await seed()

    print("\n=== SEEDED LEARNER DATA ===")
    print("User:", USER_ID)

    # ---------------------------------------------------------------
    # 2. Build the LangGraph.
    # ---------------------------------------------------------------

    app = build_question_gen_graph()

    # ---------------------------------------------------------------
    # 3. Initial graph state.
    #
    # learning_state starts empty intentionally.
    # load_memory_node must populate it from the database.
    # ---------------------------------------------------------------

    initial_state = {
        "user_id": USER_ID,
        "topic": "",
        "notes": (
            "Stereochemistry is the study of the three-dimensional "
            "arrangement of atoms in molecules. Chiral molecules and "
            "enantiomers are important concepts."
        ),
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

    config = {
        "configurable": {
            "thread_id": "memory-integration-test-1"
        }
    }

    # ---------------------------------------------------------------
    # 4. Execute the async graph.
    # ---------------------------------------------------------------

    final_state = await app.ainvoke(
        initial_state,
        config=config,
    )

    # ---------------------------------------------------------------
    # 5. Display what memory reached the planner.
    # ---------------------------------------------------------------

    print("\n=== MEMORY LOADED INTO GRAPH ===")

    learning_state = final_state["learning_state"]

    print(
        "Retention:",
        learning_state["retention_by_topic"],
    )

    print(
        "Weak topics:",
        learning_state["weak_topics"],
    )

    print(
        "Due questions:",
        learning_state["due_questions"],
    )

    print(
        "Feynman gaps:",
        learning_state["feynman_gaps"],
    )

    # ---------------------------------------------------------------
    # 6. Display adaptive decision.
    # ---------------------------------------------------------------

    print("\n=== ADAPTIVE PLANNER DECISION ===")

    print(
        "Activity:",
        final_state["selected_activity"],
    )

    print(
        "Topic:",
        final_state["selected_topic"],
    )

    print(
        "Difficulty:",
        final_state["selected_difficulty"],
    )

    print(
        "Reason:",
        final_state["decision_reason"],
    )

    # ---------------------------------------------------------------
    # 7. Display execution trace.
    # ---------------------------------------------------------------

    print("\n=== AGENT TRACE ===")

    for line in final_state["attempt_log"]:
        print(" -", line)

    # ---------------------------------------------------------------
    # 8. Assertions.
    #
    # These turn the demo into an actual integration test.
    # ---------------------------------------------------------------

    assert learning_state["retention_by_topic"]

    assert learning_state["weak_topics"]

    assert "Organic Chemistry" in learning_state["retention_by_topic"]

    assert (
        learning_state["retention_by_topic"]["Organic Chemistry"]
        == 32.5
    )

    assert final_state["selected_activity"] in {
        "feynman",
        "retrieval",
        "elaboration",
    }

    assert final_state["selected_topic"]

    print("\n=== RESULT ===")
    print(
        "PASS: persistent learner memory successfully "
        "influenced the LangGraph workflow."
    )


if __name__ == "__main__":
    asyncio.run(main())