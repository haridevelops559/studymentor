"""
Integration test for learner memory.

The seed and memory-loading operations intentionally run in the same
Python process because the default development database is in-memory.

This verifies:

    seed data
        ↓
    database collections
        ↓
    learner memory service
        ↓
    structured learning state
"""

from __future__ import annotations

import asyncio

from app.agents.memory.learner_memory import build_learner_memory
from app.agents.memory.seed_memory_demo import seed


async def main() -> None:
    print("=" * 50)
    print("LEARNER MEMORY INTEGRATION TEST")
    print("=" * 50)

    # Seed and read in the SAME process.
    await seed()

    print("\n=== LOADING LEARNER MEMORY ===")

    memory = await build_learner_memory("demo-user")

    print("\nRetention:")
    print(memory["retention_by_topic"])

    print("\nWeak topics:")
    print(memory["weak_topics"])

    print("\nDue questions:")
    print(memory["due_questions"])

    print("\nDue breakdown:")
    print(memory["due_breakdown"])

    print("\nRecent reviews:")
    print(memory["recent_reviews"])

    print("\nFeynman gaps:")
    print(memory["feynman_gaps"])

    # Basic assertions.
    assert "Organic Chemistry" in memory["retention_by_topic"]
    assert "Modern Physics" in memory["retention_by_topic"]
    assert "Evolutionary Biology" in memory["retention_by_topic"]

    assert memory["retention_by_topic"]["Organic Chemistry"] == 32.5
    assert memory["retention_by_topic"]["Modern Physics"] == 67.5
    assert memory["retention_by_topic"]["Evolutionary Biology"] == 90.0

    assert len(memory["weak_topics"]) == 3
    assert memory["due_questions"] == 2

    assert "chirality" in memory["feynman_gaps"]
    assert "enantiomers" in memory["feynman_gaps"]
    assert "threshold frequency" in memory["feynman_gaps"]

    print("\n=== RESULT ===")
    print("PASS: learner memory loaded and derived correctly.")


if __name__ == "__main__":
    asyncio.run(main())