# Agent Layer Guide — Ollama + LangChain + LangGraph

This layer bolts an experimental Ollama/LangChain/LangGraph "AI question
generation" feature onto StudyMentor, without touching the core (tested,
working) app. It's designed to be **learned file-by-file, in your own
terminal, with a git commit after each one** — not run all at once.

**Nothing here executed in the environment that built this repo** — there's
no local Ollama server or internet access to pull model weights in that
sandbox. Every file was written to compile cleanly and has a documented,
inspectable purpose, but **you** are the one who proves it runs, by
following the steps below. That's deliberate: the exploration/experimentation
process itself is the resume-worthy part, not just having the files exist.

---

## 0. One-time local setup

```bash
# 1. Install Ollama (https://ollama.com) — a local LLM runtime.
#    macOS: brew install ollama   |   or download from ollama.com

# 2. Pull a small, fast model — 1B params runs on almost any laptop.
ollama pull llama3.2:1b

# 3. Start the server (often auto-starts; if not:)
ollama serve

# 4. In a new terminal, from the project root:
cd studymentor/backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-agents.txt

# 5. Start a fresh git repo for this exercise, if you haven't already
cd ../..
git init
git add .
git commit -m "chore: initial StudyMentor + agent-layer scaffold"
```

---

## 1. Folder structure with file-by-file overview

```text
backend/
├── requirements-agents.txt      Optional deps (langchain-core, langchain-ollama,
│                                 langgraph) — separate from requirements.txt so the
│                                 core API never depends on this experimental layer.
│
├── app/
│   ├── routers/
│   │   └── agents.py            The ONE seam connecting this layer to the real API.
│   │                             Exposes POST /api/agents/generate-questions, import-
│   │                             guards langchain so a missing dep degrades to a 503
│   │                             instead of crashing the whole app at startup.
│   │
│   └── agents/
│       ├── llm.py                get_llm(): wraps ChatOllama behind one function, so
│       │                          every other file depends on this, not on
│       │                          langchain_ollama directly. Swap models/providers here.
│       │
│       ├── prompts.py             ChatPromptTemplate objects for question-generation
│       │                          and Feynman-feedback — separates prompt *shape* from
│       │                          the data filled into it at call time.
│       │
│       ├── parsers.py             PydanticOutputParser turning raw LLM text into a
│       │                          validated GeneratedQuestionBatch object — reuses the
│       │                          same shape the real /api/questions endpoint expects.
│       │
│       ├── tools.py               @tool-decorated functions wrapping the app's OWN
│       │                          already-tested pure functions (scheduler, analytics)
│       │                          so an LLM agent calls verified math, not guesses.
│       │
│       ├── memory.py               InMemoryChatMessageHistory keyed by session_id — the
│       │                          state a future "study-coach chat" feature would need
│       │                          to answer follow-up questions coherently.
│       │
│       ├── retriever.py           KeywordNoteRetriever: the simplest possible retriever
│       │                          (keyword overlap, no embeddings/vector DB) with an
│       │                          honest note on when you'd upgrade to real RAG.
│       │
│       ├── chains.py              LCEL pipelines built with the `|` operator:
│       │                          RunnableSequence (prompt|llm|parser|lambda|parser)
│       │                          and RunnableParallel (two branches at once).
│       │
│       ├── callbacks.py           A custom BaseCallbackHandler that times LLM calls —
│       │                          the hook point you'd use for production observability
│       │                          (latency/cost metrics) without modifying chains.
│       │
│       ├── graph/
│       │   ├── state.py           QuestionGenState: the typed dict that flows through
│       │   │                      every LangGraph node — the graph's single source of
│       │   │                      truth for one run.
│       │   ├── nodes.py           Four node functions (generate, critique,
│       │   │                      increment_retry, human_approval) — where the actual
│       │   │                      work happens; the graph itself has zero business logic.
│       │   └── build_graph.py     Wires nodes into a StateGraph: conditional routing,
│       │                          a bounded retry loop, MemorySaver checkpointing, a
│       │                          human-approval escape hatch, plus a SEPARATE minimal
│       │                          graph demonstrating parallel branches, and a note on
│       │                          treating a compiled graph as a reusable subgraph.
│       │
│       └── multi_agent/
│           └── orchestrator.py    Planner → Executor → Reflector, implemented in plain
│                                  Python (no framework) — deliberately placed next to
│                                  run_single_agent() doing the SAME task one-shot, so you
│                                  can compare both and articulate the trade-off. Ends
│                                  with a written comparison: LangGraph vs CrewAI vs
│                                  AutoGen, and when each earns its complexity.
│
└── agent_experiments/
    └── README.md                 Your own scratch space — copy a file here, break it,
                                   fix it, before touching the "real" one. Not imported
                                   by the app, so nothing here can break `pytest`.

docs/
└── AGENT-LAYER-GUIDE.md          This file.
```

---

## 2. Function Calling vs MCP (concept note — no code, since this app
doesn't need MCP)

- **Function calling** (what `tools.py` demonstrates): the model provider's
  API lets you describe functions (name, JSON-schema args, description);
  the model decides to call one and returns structured arguments; *your*
  code executes it and feeds the result back. Tight coupling between your
  code and the model call — the tool only exists inside that one process.
- **MCP (Model Context Protocol)**: a standardized *server* protocol for
  exposing tools/data to *any* MCP-compatible client (Claude Desktop, an
  IDE, etc.), not just one LLM call in one script. You'd reach for MCP if
  you wanted StudyMentor's scheduler/analytics tools usable from multiple
  different AI clients without rewriting the tool-calling glue for each
  one. For a single-app feature like question generation, function calling
  is the right-sized choice — MCP would be over-engineering for this scope,
  and being able to say *why* you didn't reach for it is itself a signal.

---

## 3. The iterative, reverse-engineering workflow (do this, don't skip to the website)

The point isn't to get a working chatbot fast — it's to be able to explain,
file by file, what each piece does and why it's shaped that way. Work
through this in order. **One git commit per numbered step.**

### Step 1 — Prove the LLM connection works, nothing else

```bash
cd backend && source .venv/bin/activate
python -m app.agents.llm
```
Expect: `LLM response: ready` (or close to it — small models aren't
perfectly obedient). If this fails, nothing downstream will work — debug
Ollama itself before moving on.

```bash
git add -A && git commit -m "test: confirm local Ollama connection via app.agents.llm"
```

### Step 2 — Read, then run, `prompts.py`

Before running it: open the file and predict what `filled.to_messages()`
will print. Then run:
```bash
python -m app.agents.prompts
```
Compare your prediction to the actual output. This is the "reverse
engineering" step — build a mental model, then verify it.
```bash
git commit -am "test: verify prompt template fills placeholders as expected"
```

### Step 3 — `parsers.py` (no LLM needed — pure parsing logic)
```bash
python -m app.agents.parsers
```
Try breaking it on purpose: edit `sample_llm_output` to remove a closing
brace, rerun, read the validation error. Understanding *how it fails* is as
valuable as seeing it succeed.
```bash
git commit -am "test: explore PydanticOutputParser success and failure modes"
```

### Step 4 — `tools.py` (no LLM needed)
```bash
python -m app.agents.tools
```
Then, in `agent_experiments/`, copy this file and add a third tool
wrapping `app/services/analytics.py: weakest_topics()`. Get it working
there before touching the real file.
```bash
git commit -am "experiment: add a third tool in agent_experiments/ scratch space"
```

### Step 5 — `memory.py` and `retriever.py` (no LLM needed)
```bash
python -m app.agents.memory
python -m app.agents.retriever
```
Try a retriever query that shares NO keywords with any note and confirm it
returns an empty list — that's the honest limitation of a keyword
retriever, and being able to demonstrate you found that edge case yourself
is exactly the kind of thing to mention in an interview.
```bash
git commit -am "test: confirm keyword retriever returns empty on no overlap"
```

### Step 6 — `chains.py` (requires Ollama — the first real integration test)
```bash
python -m app.agents.chains
```
If the JSON parsing fails, that's `strip_markdown_fences` doing its job —
temporarily comment it out of the chain in `build_question_generation_chain`,
rerun, and see the raw failure it was protecting against. Then put it back.
```bash
git commit -am "test: run full LCEL question-generation chain end-to-end"
```

### Step 7 — `callbacks.py` (requires Ollama)
```bash
python -m app.agents.callbacks
```
Note the printed latency. Small local models on CPU can be slow — this is
a legitimate, real observation to make about local-LLM trade-offs.
```bash
git commit -am "test: measure LLM call latency via custom callback handler"
```

### Step 8 — the LangGraph pipeline (requires Ollama)
```bash
python -m app.agents.graph.build_graph
```
Read `attempt_log` in the output — it should show at least one
`generate`/`critique` pair. Force the retry loop: temporarily make
`critique_node` in `nodes.py` always return `is_approved: False`, rerun,
and confirm you see `human_approval` get reached after `MAX_RETRIES`.
Revert the change.
```bash
git commit -am "test: force LangGraph retry loop and human-approval branch"
```

### Step 9 — the parallel-branches demo graph (requires Ollama only indirectly — this one doesn't call the LLM)
```python
# quick manual check, e.g. in a REPL:
from app.agents.graph.build_graph import build_parallel_demo_graph
g = build_parallel_demo_graph()
print(g.invoke({"notes": "Virtual memory maps pages to disk."}))
```
```bash
git commit -am "test: confirm parallel-branch graph joins both results"
```

### Step 10 — multi-agent orchestrator (requires Ollama)
```bash
python -m app.agents.multi_agent.orchestrator
```
Compare the `[single-agent]` log lines to the `[planner]/[executor]/
[reflector]` lines. Write down, in your own words, one concrete scenario
where the multi-agent version would produce a *better* result than the
single-agent version (hint: think about what happens when `execute()`
produces a weak answer for one specific topic).
```bash
git commit -am "test: compare single-agent vs planner-executor-reflector output"
```

### Step 11 — only now, wire it into the real API
```bash
uvicorn app.main:app --reload
# in another terminal:
curl -X POST localhost:8000/api/agents/generate-questions \
  -H "Content-Type: application/json" \
  -d '{"topic": "Virtual Memory", "notes": "Virtual memory lets a process use more address space than physical RAM.", "num_questions": 2}'
```
```bash
git commit -am "feat: verify agent layer reachable through the real FastAPI endpoint"
```

### Step 12 — confirm you didn't break anything
```bash
pytest -v
```
All 12 original tests should still pass — this is the whole point of
having built the agent layer as an optional, import-guarded addition
rather than modifying the core app in place.
```bash
git commit -am "test: confirm core test suite unaffected by agent layer"
```

---

## 4. What to say in an interview about this specific exercise

*"I didn't just wire up a LangChain demo — I built it as an optional layer
behind one API seam, specifically so it couldn't destabilize the tested
core product if the LLM dependency broke or wasn't installed. I tested
each concept in isolation from the terminal before integrating anything,
and I can walk through exactly where a retry loop, a human-approval branch,
or a parallel fan-out lives in the LangGraph state machine."*

That sentence, backed by real git history showing incremental, file-by-file
commits, is worth more to a recruiter than a working chatbot demo with no
evidence of how you got there.
