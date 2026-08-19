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

from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda, RunnableParallel

from app.agents.llm import get_llm
from app.agents.parsers import get_question_parser
from app.agents.prompts import QUESTION_GENERATION_PROMPT


def strip_markdown_fences(text: str) -> str:
    """A RunnableLambda step: models sometimes wrap JSON in ```json fences
    even when told not to. Strip them before the parser sees the text."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        cleaned = cleaned.removeprefix("json").strip()
    return cleaned


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
