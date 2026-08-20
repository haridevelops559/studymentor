"""
End-to-end learner-memory integration test.

Flow:

seed data
    ↓
learner memory aggregation
    ↓
memory node
    ↓
adaptive planner
"""

from __future__ import annotations

import asyncio

from app.agents.memory.seed_memory_demo import seed, USER_ID
from app.agents.memory.learner_memory import build_learner_memory
from app.agents.graph.nodes import load_memory_node


async def main():
    print("======================================")
    print("LEARNER MEMORY INTEGRATION TEST")
    print("======================================")

    # ---------------------------------------------------------------
    # 1. Seed database
    # ---------------------------------------------------------------

    await seed()

    # ---------------------------------------------------------------
    # 2. Read aggregated learner memory
    # ---------------------------------------------------------------

    memory = await build_learner_memory(user_id=USER_ID)

    print("\n=== AGGREGATED LEARNER MEMORY ===")

    print("\nRetention:")
    for topic, retention in memory["retention_by_topic"].items():
        print(f" - {topic}: {retention}%")

    print("\nWeak topics:")
    for topic in memory["weak_topics"]:
        print(
            f" - {topic['topic_id']}: "
            f"{topic['retention']}%"
        )

    print("\nDue questions:")
    print(memory["due_questions"])

    print("\nDue breakdown:")
    print(memory["due_breakdown"])

    print("\nRecent reviews:")
    print(memory["recent_reviews"])

    print("\nFeynman gaps:")
    print(memory["feynman_gaps"])

    # ---------------------------------------------------------------
    # 3. Test LangGraph memory node
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

    memory_update = await load_memory_node(state)

    print("\n=== LANGGRAPH MEMORY NODE ===")
    print(memory_update)

    # ---------------------------------------------------------------
    # 4. Assertions
    # ---------------------------------------------------------------

    assert "learning_state" in memory_update

    loaded = memory_update["learning_state"]

    assert "Organic Chemistry" in loaded["retention_by_topic"]
    assert "Modern Physics" in loaded["retention_by_topic"]
    assert "Evolutionary Biology" in loaded["retention_by_topic"]

    assert loaded["weak_topics"]

    print("\n=== RESULT ===")
    print("PASS: learner memory was loaded successfully.")


if __name__ == "__main__":
    asyncio.run(main())