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


if __name__ == "__main__":
    parser = get_question_parser()
    print("Format instructions the LLM is told to follow:\n")
    print(parser.get_format_instructions())

    # Simulate a well-formed LLM response to prove the parser round-trips.
    sample_llm_output = (
        '{"questions": [{"question": "What is virtual memory?", '
        '"answer": "A technique letting processes use more address space '
        'than physical RAM."}]}'
    )
    parsed = parser.parse(sample_llm_output)
    print("\nParsed object:", parsed)
