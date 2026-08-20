"""
Seed realistic learner data for testing persistent agent memory.

Subjects:
- Organic Chemistry
- Modern Physics
- Evolutionary Biology
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

from app.database import get_collection, reset_in_memory_db
from app.schemas.review import ReviewRating


USER_ID = "demo-user"


async def seed():
    reset_in_memory_db()

    questions = get_collection("questions")
    reviews = get_collection("reviews")
    feynman = get_collection("feynman_explanations")

    now = datetime.now(timezone.utc)

    # ---------------------------------------------------------------
    # Organic Chemistry — weak topic
    # ---------------------------------------------------------------

    organic_questions = [
        {
            "topic_id": "Organic Chemistry",
            "question": "What is stereochemistry?",
            "answer": "The study of spatial arrangement of atoms in molecules.",
            "review_count": 5,
            "correct_count": 2,
            "difficulty": 2.8,
            "next_review": now - timedelta(days=1),
        },
        {
            "topic_id": "Organic Chemistry",
            "question": "What is a chiral molecule?",
            "answer": "A molecule that is not superimposable on its mirror image.",
            "review_count": 4,
            "correct_count": 1,
            "difficulty": 3.0,
            "next_review": now,
        },
    ]

    # ---------------------------------------------------------------
    # Modern Physics — medium topic
    # ---------------------------------------------------------------

    physics_questions = [
        {
            "topic_id": "Modern Physics",
            "question": "What is the photoelectric effect?",
            "answer": "Emission of electrons when light strikes a material.",
            "review_count": 5,
            "correct_count": 3,
            "difficulty": 2.5,
            "next_review": now + timedelta(days=2),
        },
        {
            "topic_id": "Modern Physics",
            "question": "What determines the energy of a photon?",
            "answer": "Its frequency.",
            "review_count": 4,
            "correct_count": 3,
            "difficulty": 2.4,
            "next_review": now + timedelta(days=3),
        },
    ]

    # ---------------------------------------------------------------
    # Evolutionary Biology — strong topic
    # ---------------------------------------------------------------

    biology_questions = [
        {
            "topic_id": "Evolutionary Biology",
            "question": "What is natural selection?",
            "answer": "Differential survival and reproduction of organisms.",
            "review_count": 5,
            "correct_count": 5,
            "difficulty": 2.0,
            "next_review": now + timedelta(days=7),
        },
        {
            "topic_id": "Evolutionary Biology",
            "question": "What is genetic variation?",
            "answer": "Differences in genetic characteristics among individuals.",
            "review_count": 5,
            "correct_count": 4,
            "difficulty": 2.1,
            "next_review": now + timedelta(days=6),
        },
    ]

    all_questions = (
        organic_questions
        + physics_questions
        + biology_questions
    )
    for question in all_questions:
        question["user_id"] = USER_ID



    created_questions = []

    for question in all_questions:
        question["created_at"] = now
        question["last_reviewed"] = now - timedelta(days=1)

        created = await questions.insert_one(question)
        created_questions.append(created)

    # ---------------------------------------------------------------
    # Review history
    # ---------------------------------------------------------------

    ratings = {
        "Organic Chemistry": [
            ReviewRating.again,
            ReviewRating.again,
            ReviewRating.hard,
        ],
        "Modern Physics": [
            ReviewRating.hard,
            ReviewRating.good,
            ReviewRating.good,
        ],
        "Evolutionary Biology": [
            ReviewRating.good,
            ReviewRating.easy,
            ReviewRating.good,
        ],
    }

    for question in created_questions:
        topic = question["topic_id"]

        for index, rating in enumerate(ratings[topic]):
            await reviews.insert_one(
                {
                    "user_id": USER_ID,
                    "question_id": question["_id"],
                    "rating": rating.value,
                    "given_answer": "",
                    "reviewed_at": now - timedelta(days=3 - index),
                    "next_review": question["next_review"],
                }
            )

    # ---------------------------------------------------------------
    # Feynman memory
    # ---------------------------------------------------------------

    await feynman.insert_one(
        {
            "user_id": USER_ID,
            "topic_id": "Organic Chemistry",
            "explanation": (
                "Stereochemistry is about how atoms are arranged "
                "in three dimensions."
            ),
            "checklist": [
                "stereochemistry",
                "chirality",
                "enantiomers",
            ],
            "created_at": now,
            "check_result": {
                "covered": [
                    "stereochemistry",
                ],
                "missing": [
                    "chirality",
                    "enantiomers",
                ],
                "coverage_ratio": 0.33,
            },
        }
    )

    await feynman.insert_one(
        {
            "user_id": USER_ID,
            "topic_id": "Modern Physics",
            "explanation": (
                "The photoelectric effect happens when light "
                "causes electrons to leave a material."
            ),
            "checklist": [
                "photoelectric effect",
                "photon energy",
                "threshold frequency",
            ],
            "created_at": now,
            "check_result": {
                "covered": [
                    "photoelectric effect",
                    "photon energy",
                ],
                "missing": [
                    "threshold frequency",
                ],
                "coverage_ratio": 0.67,
            },
        }
    )

    print("=== MEMORY DEMO SEEDED ===")
    print("User:", USER_ID)
    print("Topics:")
    print(" - Organic Chemistry")
    print(" - Modern Physics")
    print(" - Evolutionary Biology")


if __name__ == "__main__":
    asyncio.run(seed())