"""
Prompt Templates.

Concept being explored: LangChain's PromptTemplate/ChatPromptTemplate lets
you separate the *shape* of a prompt (with typed placeholders) from the
*data* filled into it at call time -- the same "template vs data" idea as
Jinja2 for HTML, applied to LLM prompts.

Two templates here map directly onto StudyMentor's own product features
(see docs/SRS.md section 5B and the Feynman-mode feature) rather than
generic "write me a poem" toy examples, so the agent layer is actually
useful to the rest of the app.

Run: python -m app.agents.prompts
"""
from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

# Turns raw notes into retrieval-practice questions -- the "AI-generated
# questions" feature explicitly scoped out of the v1 MVP (see README.md's
# roadmap). This is where it would plug in.
QUESTION_GENERATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a study-question writer. Given a student's notes on a "
            "topic, write clear, single-fact retrieval-practice questions. "
            "Each question must have exactly one unambiguous correct answer. "
            "Favor 'what/why/how' questions over yes/no questions.",
        ),
        (
            "human",
            "Topic: {topic}\n\nNotes:\n{notes}\n\n"
            "Write {num_questions} retrieval-practice questions with answers. "
            "Respond ONLY as a JSON array of objects with 'question' and "
            "'answer' keys -- no prose, no markdown fences.",
        ),
    ]
)

# Used by the Feynman-mode self-check (app/services/scoring.py) as an
# optional LLM-assisted upgrade over the keyword-overlap heuristic --
# see docs/AGENT-LAYER-GUIDE.md for why the heuristic version ships by
# default and this is opt-in.
FEYNMAN_FEEDBACK_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You coach students using the Feynman technique. You never grade "
            "correctness with confidence you don't have -- you point out gaps "
            "and ask questions, you don't lecture.",
        ),
        (
            "human",
            "Topic: {topic}\n\nStudent's explanation:\n{explanation}\n\n"
            "Key ideas that should be covered: {checklist}\n\n"
            "In 3 sentences or fewer, note what's missing or unclear. "
            "Do not just restate the checklist.",
        ),
    ]
)


if __name__ == "__main__":
    filled = QUESTION_GENERATION_PROMPT.invoke(
        {
            "topic": "Virtual Memory",
            "notes": "Virtual memory lets a process use more address space "
            "than physical RAM by mapping pages to disk.",
            "num_questions": 2,
        }
    )
    for message in filled.to_messages():
        print(f"[{message.type}] {message.content}\n")
