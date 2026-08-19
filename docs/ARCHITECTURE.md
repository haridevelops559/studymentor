# Architecture

```text
                     Browser
                        │
                        ▼
              ┌─────────────────┐
              │     Next.js     │
              │ App Router      │
              │ React 18        │
              │ TypeScript      │
              │ Tailwind CSS    │
              └────────┬────────┘
                       │  REST (fetch)
                       ▼
              ┌─────────────────┐
              │     FastAPI     │
              │                 │
              │ Routers         │
              │ Schemas         │
              │ Services        │
              └────────┬────────┘
                       │  async collection interface
                       ▼
              ┌─────────────────┐
              │  In-memory (dev) │
              │  or MongoDB via  │
              │  Motor (prod)    │
              └─────────────────┘
```

## Frontend

- **Next.js App Router.** `app/dashboard/page.tsx` is a Server Component
  that calls the API directly at request time — fast first paint, no
  client-side spinner for the initial view.
- **Client Components** (`"use client"`) are used only where interactivity
  is required: the review loop (`app/review/page.tsx`), practice/question
  authoring, and the Feynman self-check form.
- **`lib/api.ts`** is the single place that knows about HTTP — every page
  and hook calls through `api.*`, never `fetch` directly. This keeps the
  base URL, error handling, and JSON parsing in one spot.
- **`lib/types.ts`** mirrors the backend Pydantic schemas by hand. For a
  project this size that's a deliberate, simple choice over a codegen step;
  see `docs/API.md` for the source of truth.

## Backend

- **`app/routers/*`** — thin HTTP layer: parse request, call a
  collection/service, return a schema. No business logic lives here.
- **`app/schemas/*`** — Pydantic models used for both request validation and
  response serialization.
- **`app/services/*`** — the actual business logic, deliberately separated
  from HTTP and storage so it's unit-testable in isolation:
  - `scheduler.py` — spaced-repetition interval calculation
  - `scoring.py` — retrieval-practice scoring and Feynman coverage checking
  - `analytics.py` — dashboard aggregation (retention, due counts, weak spots)
- **`app/database.py`** — a tiny async collection interface
  (`find_one`/`find`/`insert_one`/`update_one`/`delete_one`/`count`) with two
  implementations: an in-memory store (default, zero setup) and a Motor/
  MongoDB adapter (`USE_IN_MEMORY_DB=false`). Routers never know which one
  they're talking to.

## Why an in-memory backend by default

The goal is that `git clone` → `pip install -r requirements.txt` →
`uvicorn app.main:app --reload` gives you a fully working API with zero
external services, and that `pytest` runs fast and hermetically in CI
without spinning up MongoDB. Swapping to real MongoDB for production is a
one-line env var change (`USE_IN_MEMORY_DB=false` + `MONGO_URI=...`) because
routers/services only ever touch the abstract collection interface.
