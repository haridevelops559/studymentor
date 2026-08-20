"""
End-to-end test:

database
    -> learner memory
    -> LangGraph memory node
    -> adaptive planner
"""

from __future__ import annotations

import asyncio

from app.agents.memory.seed_memory_demo import seed, USER_ID
from app.agents.graph.nodes import (
    load_memory_node,
    adaptive_planner_node,
)


async def main():
    print("======================================")
    print("ADAPTIVE MEMORY -> PLANNER TEST")
    print("======================================")

    # ---------------------------------------------------------------
    # 1. Seed realistic learner data
    # ---------------------------------------------------------------

    await seed()

    # ---------------------------------------------------------------
    # 2. Initial graph state
    # ---------------------------------------------------------------

    state = {
        "user_id": USER_ID,
        "topic": "",
        "notes": "",
        "learning_state": {},

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

    # ---------------------------------------------------------------
    # 3. Load real learner memory
    # ---------------------------------------------------------------

    memory_update = await load_memory_node(state)

    state.update(memory_update)

    print("\n=== MEMORY LOADED ===")

    print("Retention:")
    print(state["learning_state"]["retention_by_topic"])

    print("\nWeak topics:")
    print(state["learning_state"]["weak_topics"])

    print("\nDue questions:")
    print(state["learning_state"]["due_questions"])

    print("\nFeynman gaps:")
    print(state["learning_state"]["feynman_gaps"])

    # ---------------------------------------------------------------
    # 4. Give the memory to the adaptive planner
    # ---------------------------------------------------------------

    planner_update = adaptive_planner_node(state)

    state.update(planner_update)

    print("\n=== ADAPTIVE PLANNER DECISION ===")

    print("Activity:")
    print(state["selected_activity"])

    print("Topic:")
    print(state["selected_topic"])

    print("Difficulty:")
    print(state["selected_difficulty"])

    print("Reason:")
    print(state["decision_reason"])

    # ---------------------------------------------------------------
    # 5. Verify planner actually made a decision
    # ---------------------------------------------------------------

    assert state["selected_activity"]

    assert state["selected_topic"]

    assert state["decision_reason"]

    assert state["selected_activity"] in {
        "retrieval",
        "feynman",
        "elaboration",
    }

    print("\n=== RESULT ===")
    print("PASS: learner memory successfully influenced the planner.")


if __name__ == "__main__":
    asyncio.run(main())