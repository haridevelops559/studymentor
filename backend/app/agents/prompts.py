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


ELABORATION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyMentor's elaboration learning coach. "
            "Your job is to deepen understanding by generating reasoning-based "
            "questions that connect ideas, causes, mechanisms, and consequences. "
            "Do not generate simple definition questions. "
            "Prefer why, how, compare, predict, and what-if questions. "
            "Every question MUST have a concise answer based only on the supplied notes."
        ),
        (
            "human",
            "Topic: {topic}\n\n"
            "Notes:\n{notes}\n\n"
            "Known learner gaps:\n{gaps}\n\n"
            "Generate {num_questions} elaboration questions.\n\n"
            "Return ONLY valid JSON in exactly this structure:\n"
            "{{\n"
            '  "questions": [\n'
            '    {{"question": "reasoning question", "answer": "concise answer"}},\n'
            '    {{"question": "reasoning question", "answer": "concise answer"}}\n'
            "  ]\n"
            "}}\n\n"
            "Every object MUST contain both 'question' and 'answer'. "
            "Do not omit the answer field. "
            "Do not return markdown fences. "
            "Do not return any prose outside the JSON."
        ),
    ]
)

LEARNING_DECISION_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are StudyMentor's adaptive learning planner. "
            "Your job is to choose the most useful learning activity "
            "for the student based on their current learning state. "
            "\n\n"
            "Available activities:\n"
            "- retrieval: use active-recall questions when material is due "
            "or the student needs retrieval practice.\n"
            "- feynman: ask the student to explain a concept in their own "
            "words when there are conceptual gaps or weak understanding.\n"
            "- elaboration: ask why/how/what-if questions when the student "
            "needs deeper conceptual understanding.\n\n"
            "Prefer the weakest topic when there is clear evidence of "
            "weakness. Do not invent student performance data. "
            "Return only the structured format requested by the parser."
        ),
        (
            "human",
            "Student learning state:\n"
            "{learning_state}\n\n"
            "Choose exactly one learning activity, the most appropriate "
            "topic, an appropriate difficulty from 1.0 to 3.5, and a short "
            "reason explaining the decision.\n\n"
            "{format_instructions}",
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
