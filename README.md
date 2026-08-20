# StudyMentor — Personal Learning & Retention Coach

A study workflow inspired by research on retrieval practice, distributed practice,
self-explanation and other learning techniques. StudyMentor turns notes into
active-recall questions, schedules spaced reviews, and gives you a Feynman-style
"explain it back" workflow — with a dashboard that tracks retention over time.

> This is **not** a "scientifically proven learning system." It's a workflow
> **inspired by** learning-science research. See `docs/LEARNING-SCIENCE.md`.

## Stack

| Layer    | Tech |
|----------|------|
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS |
| Backend  | FastAPI, Pydantic, pytest |
| Database | MongoDB (Motor) in production; in-memory async store for local dev/tests |
| CI       | GitHub Actions (lint + build + test on every PR) |

## Monorepo layout

```
studymentor/
├── frontend/     Next.js app (dashboard, review, practice, feynman)
├── backend/      FastAPI service (routers, schemas, services, tests)
├── docs/         SRS, architecture, API reference, learning-science notes
└── .github/      CI workflows, issue templates, PR template
```

## Quick start

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:3000

The frontend talks to the backend via `NEXT_PUBLIC_API_URL` (defaults to
`http://localhost:8000/api` — see `frontend/.env.example`).

### Run backend tests

```bash
cd backend
pytest -v
```

## Core learning loop

```
Capture notes → Generate questions → Retrieval practice → Rate recall
   → Spaced-repetition scheduler → Feynman explanation → Dashboard analytics
```

## Engineering highlights

- Next.js Server Components for data-heavy views, Client Components for
  interactive retrieval/timer sessions
- Typed API contract shared via `frontend/lib/types.ts`
- FastAPI routers/schemas/services separation with Pydantic validation
- A simple, testable spaced-repetition scheduler (`backend/app/services/scheduler.py`)
- Retention analytics aggregation (`backend/app/services/analytics.py`)
- GitHub Actions CI for both frontend and backend
- Feature-branch + PR workflow templates under `.github/`

## Optional: Ollama + LangChain + LangGraph agent layer

`backend/app/agents/` adds an experimental, import-guarded "AI-generated
question" feature on top of a local Ollama model — LCEL chains, tools,
memory, a retriever, and a LangGraph state machine with a retry loop,
checkpointing, and a human-approval branch, plus a Planner/Executor/
Reflector multi-agent comparison. It's wired into the API through one seam
(`POST /api/agents/generate-questions`) and degrades to a clean 503 if its
optional dependencies aren't installed — the core app and its test suite
never depend on it. See `docs/AGENT-LAYER-GUIDE.md` for setup and a
file-by-file, terminal-first, git-commit-per-step way to actually learn it.


## What I Explored & Implemented

| Concept | Implementation |
|---|---|
| **LangChain LLM pipelines** | Prompt → Ollama LLM → Pydantic structured output |
| **Structured generation** | Typed schemas and validation for agent outputs |
| **LLM Tool Calling** | Model-selected `summarize_weak_topics` and `compute_next_review` tools |
| **Tool execution loop** | `AIMessage → Tool → ToolMessage → AIMessage` |
| **LangGraph State** | Typed `QuestionGenState` shared across workflow nodes |
| **Conditional routing** | Planner dynamically selects Retrieval / Feynman / Elaboration |
| **Agent retries** | Critic → bounded retry → regeneration |
| **Checkpointing** | `MemorySaver` + `thread_id` |
| **Persistent memory** | Learner history → retention / weak topics / due reviews / Feynman gaps |
| **Specialist workflows** | Retrieval, Feynman and Elaboration activities |
| **Deterministic evaluation** | Feynman coverage and question-quality checks |
| **Human-in-the-loop** | Retry exhaustion → human-review state |
| **Async orchestration** | Async memory node + LangGraph `ainvoke()` |

## Architecture

```text
FastAPI Backend
      │
      ├── Analytics / Scheduler
      │
      ├── Database
      │      │
      │      ▼
      │  Learner Memory
      │      │
      │      ▼
      │  LangGraph State
      │      │
      │      ▼
      │  Adaptive Planner
      │      │
      │   ┌──┼──────────┐
      │   ▼  ▼          ▼
      │ Retrieval Feynman Elaboration
      │   └──┼──────────┘
      │      ▼
      │    Critic
      │      │
      │   Approved / Retry
      │      │
      │      ▼
      │ Human Review
      │
      └── LLM layer: LangChain + Ollama

