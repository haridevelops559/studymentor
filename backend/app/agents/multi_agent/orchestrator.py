"""
Single vs Multi-Agent, Planner vs Executor, Reflection vs Critic.

Concept being explored: this module implements the SAME task
("turn a subject's raw notes into a full study session: questions + a
weak-topic summary") twice, so you can point at both and explain the
trade-off instead of just asserting one is "better":

  - `run_single_agent()`   : one LLM call does planning + execution +
    self-check all at once, via one big prompt.
  - `run_multi_agent()`    : three specialized roles, each a smaller/more
    constrained prompt, coordinated by plain Python control flow (no
    framework needed for this scale -- see the note at the bottom on when
    you'd actually reach for LangGraph/CrewAI/AutoGen instead).

    Planner   -> decides *what* to do (which topics need questions, in
                 what order), doesn't touch content generation.
    Executor  -> does the actual work (calls the question-generation
                 chain from app/agents/chains.py) for each planned item.
    Reflector -> a Critic that reviews the Executor's output against a
                 rule (reusing `critique_node`'s logic) and can request
                 a redo -- this is the "Reflection" pattern: an agent
                 evaluating another agent's work product, not just
                 evaluating its own single response.

Run: python -m app.agents.multi_agent.orchestrator
"""
from __future__ import annotations

from dataclasses import dataclass, field

from app.agents.chains import build_question_generation_chain
from app.agents.graph.nodes import critique_node


@dataclass
class StudySessionPlan:
    topics_in_order: list[str]
    reasoning: str


@dataclass
class StudySessionResult:
    questions_by_topic: dict[str, list[dict]] = field(default_factory=dict)
    retries_used: int = 0
    log: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Single-agent version
# ---------------------------------------------------------------------------


def run_single_agent(topic_notes: dict[str, str]) -> StudySessionResult:
    """
    One agent (in practice: one chain, invoked per topic) does planning
    (implicit -- it just processes topics in dict order) and execution in
    one step, with no separate critique pass. Simple, fewer moving parts,
    but no self-correction if a generation is weak.
    """
    result = StudySessionResult()
    chain = build_question_generation_chain()

    for topic, notes in topic_notes.items():
        output = chain.invoke({"topic": topic, "notes": notes, "num_questions": 2})
        result.questions_by_topic[topic] = [q.model_dump() for q in output.questions]
        result.log.append(f"[single-agent] generated questions for '{topic}'")

    return result


# ---------------------------------------------------------------------------
# Multi-agent version: Planner -> Executor -> Reflector
# ---------------------------------------------------------------------------


def plan(topic_notes: dict[str, str], weakest_topic: str | None) -> StudySessionPlan:
    """Planner: decide order. Deliberately simple deterministic logic here
    rather than an LLM call -- planning THIS task doesn't need a model,
    and using plain code where you can is itself a decision worth being
    able to defend (not every step in an agentic system needs to be an
    LLM call)."""
    topics = list(topic_notes.keys())
    if weakest_topic and weakest_topic in topics:
        topics.remove(weakest_topic)
        topics.insert(0, weakest_topic)
    return StudySessionPlan(
        topics_in_order=topics,
        reasoning=(
            f"Prioritized '{weakest_topic}' first based on dashboard retention data."
            if weakest_topic
            else "No retention data yet; processing topics in given order."
        ),
    )


def execute(topic: str, notes: str) -> list[dict]:
    """Executor: does the one thing it's told to do -- generate questions
    for a single topic. Doesn't decide ordering or judge its own output."""
    chain = build_question_generation_chain()
    output = chain.invoke({"topic": topic, "notes": notes, "num_questions": 2})
    return [q.model_dump() for q in output.questions]


def reflect(topic: str, questions: list[dict]) -> tuple[bool, str]:
    """Reflector/Critic: judges another agent's output using the SAME rule
    as the LangGraph critique_node (app/agents/graph/nodes.py), reused
    here rather than duplicated -- one source of truth for "what makes a
    question good enough"."""
    fake_state = {"draft_questions": questions}
    critique_result = critique_node(fake_state)  # type: ignore[arg-type]
    return critique_result["is_approved"], critique_result["critique"]


def run_multi_agent(
    topic_notes: dict[str, str], weakest_topic: str | None = None, max_retries: int = 1
) -> StudySessionResult:
    result = StudySessionResult()

    session_plan = plan(topic_notes, weakest_topic)
    result.log.append(f"[planner] order: {session_plan.topics_in_order}")
    result.log.append(f"[planner] reasoning: {session_plan.reasoning}")

    for topic in session_plan.topics_in_order:
        notes = topic_notes[topic]
        attempt = 0
        while True:
            questions = execute(topic, notes)
            result.log.append(f"[executor] generated {len(questions)} for '{topic}'")

            approved, critique = reflect(topic, questions)
            result.log.append(f"[reflector] {critique}")

            if approved or attempt >= max_retries:
                result.questions_by_topic[topic] = questions
                result.retries_used += attempt
                break
            attempt += 1

    return result


# ---------------------------------------------------------------------------
# When to reach for a framework (LangGraph / CrewAI / AutoGen) instead of
# plain Python control flow like above -- notes, not code:
#
# The orchestration above is < 40 lines of plain Python and that's a
# feature, not a gap: for 3 fixed roles with a linear/bounded-retry flow,
# a framework adds indirection without adding capability.
#
# Reach for LangGraph when you need: persistent checkpointing across
# process restarts, human-in-the-loop pausing, or a graph shape too
# complex to read as nested loops (see app/agents/graph/build_graph.py --
# that DOES use LangGraph, because the retry-loop + human-approval
# branching genuinely benefits from a declarative graph and checkpointer).
#
# CrewAI vs AutoGen vs LangGraph (comparison, for when asked):
#   - CrewAI  : highest-level abstraction -- you declare Agents (role,
#     goal, backstory) and Tasks, CrewAI handles delegation. Fastest to
#     prototype a Planner/Executor/Reflector crew, least control over the
#     exact execution graph.
#   - AutoGen : conversation-centric -- agents are chat participants that
#     message each other; strong for the "let two agents debate/refine"
#     pattern, less natural for a strict linear pipeline like this one.
#   - LangGraph: lowest-level of the three -- you define the exact graph
#     (nodes/edges/state), which is more code but gives full control over
#     retries, branching, and persistence, which is why it's what's
#     actually used in app/agents/graph/ for the part of this project that
#     needed that control.
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    demo_notes = {
        "Operating Systems": "Virtual memory lets a process use more "
        "address space than physical RAM by mapping pages to disk.",
        "React Hooks": "useState and useEffect let function components "
        "hold state and run side effects.",
    }

    print("=== Single-agent run ===")
    single_result = run_single_agent(demo_notes)
    for line in single_result.log:
        print(line)

    print("\n=== Multi-agent run (Planner -> Executor -> Reflector) ===")
    multi_result = run_multi_agent(demo_notes, weakest_topic="Operating Systems")
    for line in multi_result.log:
        print(line)
    print(f"\nRetries used: {multi_result.retries_used}")
