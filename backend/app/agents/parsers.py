"""
Output Parsers.

Concept being explored: an LLM's raw output is just text. An output parser
turns that text into a typed, validated Python object -- and, critically,
tells the LLM *how* to format its response in the first place via
`get_format_instructions()`, which you inject into the prompt.

We reuse the exact Pydantic schema the rest of the app already trusts
(`app.schemas.question.QuestionCreate`-shaped data) rather than inventing a
separate "AI question" shape, so anything the agent generates can be
inserted through the same `POST /api/questions` path with no adapter code.

Run: python -m app.agents.parsers
"""
from __future__ import annotations
from typing import Literal
from pydantic import BaseModel, Field


class GeneratedQuestion(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(..., min_length=1)


class GeneratedQuestionBatch(BaseModel):
    questions: list[GeneratedQuestion]


def get_question_parser():
    """
    A PydanticOutputParser bound to GeneratedQuestionBatch. Using this
    (rather than manually calling json.loads on the LLM's text) means a
    malformed response raises a clear validation error you can retry on,
    instead of an unhandled JSONDecodeError deep in a route handler.
    """
    from langchain_core.output_parsers import PydanticOutputParser

    return PydanticOutputParser(pydantic_object=GeneratedQuestionBatch)




class LearningDecision(BaseModel):
    activity: Literal[
        "retrieval",
        "feynman",
        "elaboration",
    ]
    topic: str = Field(..., min_length=1)
    difficulty: float = Field(..., ge=1.0, le=3.5)
    reason: str = Field(..., min_length=1)


def get_learning_decision_parser():
    """
    Pydantic parser for the adaptive learning planner.

    The LLM must choose one supported learning activity and return
    structured, validated data instead of free-form text.
    """
    from langchain_core.output_parsers import PydanticOutputParser

    return PydanticOutputParser(pydantic_object=LearningDecision)


if __name__ == "__main__":
    parser = get_question_parser()

    print("=== QUESTION PARSER ===")
    print("Format instructions:\n")
    print(parser.get_format_instructions())

    sample_llm_output = (
        '{"questions": [{"question": "What is virtual memory?", '
        '"answer": "A technique letting processes use more address space '
        'than physical RAM."}]}'
    )

    parsed = parser.parse(sample_llm_output)
    print("\nParsed question object:", parsed)

    print("\n=== LEARNING DECISION PARSER ===")

    decision_parser = get_learning_decision_parser()

    sample_decision = (
        '{"activity": "feynman", '
        '"topic": "Virtual Memory", '
        '"difficulty": 2.0, '
        '"reason": "The student has a conceptual gap that should be explained in their own words."}'
    )

    decision = decision_parser.parse(sample_decision)

    print("\nParsed learning decision:", decision)
    print("\nDecision format instructions:\n")
    print(decision_parser.get_format_instructions())