"""
LCEL, Runnable, RunnableSequence, RunnableParallel, RunnableLambda.

Concept being explored: LCEL ("LangChain Expression Language") is
LangChain's `|` pipe-operator syntax for composing Runnables -- every
prompt, LLM, parser, and plain function used this way implements the same
`Runnable` interface (`.invoke()`, `.batch()`, `.stream()`).

  - RunnableSequence  -> `a | b | c` (built automatically by the `|` operator)
  - RunnableParallel   -> `{"x": chain_x, "y": chain_y}` (run branches concurrently)
  - RunnableLambda     -> wrap a plain Python function so it composes with `|`

This file builds the actual "notes -> generated questions" chain used by
the question-generation feature, as a single composed pipeline instead of
imperative glue code.

Run: python -m app.agents.chains   (requires Ollama running locally)
"""
from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser, PydanticOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

from app.agents.llm import get_llm
from app.agents.parsers import (
    get_question_parser,
    get_learning_decision_parser,
    get_elaboration_parser,
)
from app.agents.prompts import (
    QUESTION_GENERATION_PROMPT,
    LEARNING_DECISION_PROMPT,
    FEYNMAN_FEEDBACK_PROMPT,
    ELABORATION_PROMPT,
)


def strip_markdown_fences(text: str) -> str:
    """
    Normalize common JSON formatting mistakes from local LLMs.

    Handles:
    1. Markdown JSON fences:
           ```json
           {...}
           ```

    2. Question batches returned as a bare array:
           [{...}, {...}]
       -> {"questions": [{...}, {...}]}

    3. Pydantic/JSON-schema wrapper returned by some models:
           {"properties": {...}}
       -> {...}
    """
    import json

    cleaned = text.strip()

    # Remove markdown fences.
    if cleaned.startswith("```"):
        parts = cleaned.split("```")

        if len(parts) >= 2:
            cleaned = parts[1].strip()

            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        return cleaned

    # Question-generation model sometimes returns a bare array.
    if isinstance(parsed, list):
        return json.dumps({"questions": parsed})

    # Some local models incorrectly reproduce the JSON-schema
    # "properties" wrapper.
    if (
        isinstance(parsed, dict)
        and set(parsed.keys()) == {"properties"}
        and isinstance(parsed["properties"], dict)
    ):
        parsed = parsed["properties"]

    return json.dumps(parsed)

def build_question_generation_chain():
    """
    RunnableSequence via the `|` operator:
        prompt -> llm -> string-parser -> strip-fences (lambda) -> pydantic-parser
    Every stage's output becomes the next stage's input, and the whole
    thing is itself a Runnable you can `.invoke()` or `.stream()`.
    """
    llm = get_llm()
    parser = get_question_parser()

    chain = (
        QUESTION_GENERATION_PROMPT
        | llm
        | StrOutputParser()
        | RunnableLambda(strip_markdown_fences)
        | parser
    )
    return chain

def build_learning_decision_chain():
    """
    Adaptive planner chain:

        learning state
            ↓
        planner prompt
            ↓
        local LLM
            ↓
        string parser
            ↓
        Pydantic LearningDecision parser
    """
    llm = get_llm()
    parser = get_learning_decision_parser()

    prompt = LEARNING_DECISION_PROMPT.partial(
        format_instructions=parser.get_format_instructions()
    )

    return (
        prompt
        | llm
        | StrOutputParser()
        | RunnableLambda(strip_markdown_fences)
        | parser
    )

def build_elaboration_chain():
    """
    Build the elaboration specialist chain.

    Flow:

        topic + notes + learner gaps
                    ↓
               LLM reasoning
                    ↓
             JSON normalization
                    ↓
             Pydantic validation
    """
    llm = get_llm()
    parser = get_elaboration_parser()

    return (
        ELABORATION_PROMPT
        | llm
        | StrOutputParser()
        | RunnableLambda(strip_markdown_fences)
        | parser
    )

def build_parallel_summary_chain():
    """
    RunnableParallel: run two independent LLM calls concurrently and
    combine their results into one dict, instead of awaiting them
    sequentially. Useful when a dashboard-style view needs several
    independent LLM-derived summaries at once.
    """
    llm = get_llm()

    tone_summary = (
        QUESTION_GENERATION_PROMPT.partial(num_questions="1")
        | llm
        | StrOutputParser()
    )
    # A second, trivial branch to demonstrate the parallel shape without
    # needing a second real prompt.
    word_count = RunnableLambda(lambda inputs: len(inputs["notes"].split()))

    return RunnableParallel(sample_question=tone_summary, notes_word_count=word_count)
def build_feynman_feedback_chain():
    """
    Build the optional LLM feedback chain for Feynman explanations.

    Flow:
        prompt -> LLM -> string parser

    The deterministic check_feynman_coverage() function remains the source
    of truth for coverage. This LLM only turns the detected gaps into
    concise coaching feedback.
    """
    llm = get_llm()

    return (
        FEYNMAN_FEEDBACK_PROMPT
        | llm
        | StrOutputParser()
    )

if __name__ == "__main__":
    sample_input = {
        "topic": "Virtual Memory",
        "notes": (
            "Virtual memory lets a process use more address space than "
            "physical RAM by mapping pages to disk. Page faults occur "
            "when a needed page isn't in physical memory."
        ),
        "num_questions": 2,
    }

    print("== RunnableSequence: full question-generation chain ==")
    chain = build_question_generation_chain()
    result = chain.invoke(sample_input)
    print(result)

    print("\n== RunnableParallel: two branches at once ==")
    parallel_chain = build_parallel_summary_chain()
    parallel_result = parallel_chain.invoke(sample_input)
    print(parallel_result)
    print("\n== Adaptive learning decision ==")

    learning_state = {
        "weak_topics": [
            {"topic_id": "os", "retention": 52.0}
        ],
        "due_questions": 4,
        "recent_reviews": [
            {"rating": "again"},
            {"rating": "hard"},
            {"rating": "again"},
        ],
        "feynman_gaps": [
            "page fault"
        ],
    }

    decision_chain = build_learning_decision_chain()

    decision = decision_chain.invoke(
        {
            "learning_state": str(learning_state),
        }
    )

    print("Learning decision:")
    print(decision)