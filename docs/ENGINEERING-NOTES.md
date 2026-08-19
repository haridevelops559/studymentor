# Engineering Notes — Decisions, System Design, and How to Navigate This Repo

This doc exists for one purpose: when a recruiter or interviewer asks
*"walk me through how you built this"*, you should be able to talk about
**decisions and trade-offs you made and tested**, not just list technologies.
Everything below points at a real file in this repo so you can open it and
speak from the code.

---

## Part 1 — 15 decisions, implementations, and experiments

Each one has: the decision, what a naive/first-pass version would have
looked like, why you didn't ship that, and the file to point at.

### Domain-based (learning-science / product engineering)

**1. Flat interval ladder vs. full SM-2 spaced-repetition algorithm**
Naive approach: implement full SM-2 (variable ease, exact interval formula)
on day one. Decision: ship a simple 4-point ladder (`again/hard/good/easy` →
fixed days) that *graduates* into ease-factor scaling only after 3 reviews.
Why: a scheduler is worth nothing if it's wrong and untestable — the simple
version is provably correct and unit-tested, and the ease-factor hook
(`update_difficulty`) is already there to grow into real SM-2 later.
→ `backend/app/services/scheduler.py`

**2. Bounding the ease factor (`MIN_EASE`/`MAX_EASE`)**
Experiment: what happens if a student rates "again" 20 times in a row?
Without clamping, the ease factor drifts toward zero/negative and intervals
either vanish or blow up. Decision: clamp to `[1.3, 3.5]`, verified with a
test that hammers the function 20 times in each direction.
→ `test_ease_factor_clamped_within_bounds` in `backend/tests/test_scheduler.py`

**3. Keyword-overlap Feynman check instead of an LLM grader**
Decision: don't call an AI model to "grade" self-explanations for v1.
Why: self-explanation's value is the student noticing their *own* gaps —
an AI silently filling gaps in interpretation would undermine that. A
transparent, inspectable keyword-overlap heuristic is honest about what
it does and doesn't verify (coverage, not correctness).
→ `backend/app/services/scoring.py: check_feynman_coverage`

**4. Refusing to overclaim technique efficacy in product copy**
Decision: maintain a dedicated doc mapping each feature to its evidence
strength (retrieval/spacing = high; interleaving/self-explanation =
moderate; mnemonics = context-dependent) so no future PR ships a claim like
"scientifically proven to improve your grades."
→ `docs/LEARNING-SCIENCE.md`

**5. Single aggregated dashboard endpoint vs. N client-side requests**
Naive: frontend fires 4 separate requests (due counts, retention, weak
topics, today's stats) on page load — four round trips, four loading
states, and a harder-to-reason-about race for "is the page ready?".
Decision: one `/api/dashboard` endpoint that aggregates server-side.
→ `backend/app/routers/dashboard.py`, consumed by `frontend/app/dashboard/page.tsx`

### Tool/technology-based

**6. Adapter pattern for storage instead of hard-coding Mongo**
Decision: write a tiny async interface (`find_one/find/insert_one/...`)
with two implementations — `InMemoryCollection` and `MotorCollectionAdapter`
— selected by one config flag. Experiment: verified that swapping backends
requires zero router/service changes, only `USE_IN_MEMORY_DB`.
→ `backend/app/database.py`

**7. Pydantic schema separation (Create vs full model)**
Decision: `QuestionCreate` (what the client sends) is a strict subset of
`Question` (what's stored/returned, including scheduler-owned fields like
`next_review`). Prevents a client from ever setting `review_count` or
`difficulty` directly through the API — those are server-owned invariants.
→ `backend/app/schemas/question.py`

**8. Server Components vs. Client Components split in Next.js**
Decision, deliberately, not by default: the dashboard is a Server Component
(`await api.dashboard.get()` runs on the server, no loading spinner needed,
smaller client JS bundle) while the review/practice/Feynman flows are
Client Components (`"use client"`) because they need `useState`/interaction.
Tested by checking the build output's route table (`ƒ` dynamic vs `○`
static) to confirm the split actually happened.
→ `frontend/app/dashboard/page.tsx` vs `frontend/app/review/page.tsx`

**9. One typed API client instead of scattered `fetch` calls**
Decision: every network call goes through `lib/api.ts`, never a raw
`fetch` in a component. Why: centralizes the base URL, JSON headers, and
error handling (`ApiError`) in one place, and every call site gets
TypeScript autocomplete instead of stringly-typed URLs.
→ `frontend/lib/api.ts`

**10. Testing strategy: unit tests for pure logic, integration tests for HTTP**
Decision: `scheduler.py`/`scoring.py`/`analytics.py` are pure functions
tested directly with no HTTP involved (fast, deterministic). Full flows
(create subject → topic → question → review → verify reschedule) are
tested through the real FastAPI app via `httpx.ASGITransport`, which
exercises routing, validation, and the database layer together.
→ `backend/tests/test_scheduler.py` (unit) vs `backend/tests/test_reviews.py` (integration)

**11. Path-filtered CI instead of one monolithic pipeline**
Decision: `backend-ci.yml` and `frontend-ci.yml` each trigger only on
changes under their own directory (`paths: ["backend/**"]`). Experiment/
reasoning: in a monorepo, a frontend-only PR shouldn't burn CI minutes
spinning up a Python environment, and vice versa.
→ `.github/workflows/backend-ci.yml`, `.github/workflows/frontend-ci.yml`

**12. Custom `ApiError` class instead of throwing raw `Response` objects**
Decision: `lib/api.ts`'s `request()` helper throws a typed `ApiError` with
a `.status` field on any non-2xx response, so every page's `catch` block
can branch on `error instanceof ApiError` and show a specific message
instead of a generic "something went wrong."
→ `frontend/lib/api.ts`, consumed in `frontend/app/dashboard/page.tsx`

**13. Zero-config local dev as a deliberate trade-off**
Decision: default to the in-memory store rather than requiring Docker/
MongoDB to run the app at all. Trade-off acknowledged explicitly: this
sacrifices dev/prod parity for onboarding speed and hermetic CI — worth it
for an MVP, and the Motor adapter exists specifically so this doesn't
become permanent technical debt.
→ `backend/app/config.py: use_in_memory_db`

**14. Domain-specific design tokens instead of default Tailwind palette**
Decision: added a `recall` color scale (`again/hard/good/easy`) to
`tailwind.config.ts` rather than hardcoding red/amber/green/blue classes
inline. Any future component that needs "the rating colors" references
one source of truth.
→ `frontend/tailwind.config.ts`, used in `frontend/components/review/RatingButtons.tsx`

**15. Multi-stage Docker build for the frontend**
Decision: two-stage Dockerfile (`builder` installs deps + runs `next build`,
final stage copies only `.next`, `node_modules`, and `public`) rather than
a single-stage image. Reasoning to have ready for an interview: smaller
final image, no dev dependencies or source maps shipped to production.
→ `frontend/Dockerfile`

---

## Part 2 — 15 system design concepts, each tied to a tool in this repo

| # | Concept | Where it shows up | Why it matters here |
|---|---------|--------------------|----------------------|
| 1 | **Separation of concerns / layered architecture** | `backend/app/routers` (HTTP) → `schemas` (validation) → `services` (logic) → `database.py` (storage) | Each layer can change without touching the others — e.g. swap Mongo for Postgres without touching scheduling logic |
| 2 | **Adapter / Repository pattern** | `database.py`: `InMemoryCollection` + `MotorCollectionAdapter` behind one interface | Business logic depends on an abstraction, not a concrete database driver |
| 3 | **Dependency inversion** | Routers call `get_collection(name)`, never `motor` or a dict directly | High-level modules (routers) don't depend on low-level details (which DB) |
| 4 | **Idempotent, pure business logic for testability** | `scheduler.py`, `scoring.py` are pure functions (same input → same output, no I/O) | Lets you unit-test the *algorithm* without a database or HTTP server at all |
| 5 | **API Gateway-style aggregation endpoint** | `GET /api/dashboard` combines 3+ data sources into one response | Reduces client round trips and moves aggregation cost to the server, which is closer to the data |
| 6 | **Statelessness of REST APIs** | Every FastAPI route reads everything it needs from the request + DB, no server-side session state | Any backend instance can serve any request — this is what makes horizontal scaling possible later |
| 7 | **CORS as an explicit trust boundary** | `app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins)` in `main.py` | Forces you to name exactly which origins can call the API instead of `*` in production |
| 8 | **Client-server rendering trade-off (SSR vs CSR)** | Dashboard = Server Component (data fetched server-side); Review = Client Component (fetched client-side after interaction) | Classic system-design trade-off: latency/SEO/bundle-size vs. interactivity |
| 9 | **Caching and cache invalidation** | `cache: "no-store"` in `lib/api.ts`, `export const dynamic = "force-dynamic"` on pages that must always be fresh | Dashboard/review data is mutated constantly (every review call) — stale caches would show wrong due-counts |
| 10 | **Optimistic vs. pessimistic UI updates** | `useDueQuestions.rate()` advances to the next question *after* the server call settles (pessimistic), but still advances even if the save errors (graceful degradation) | A conscious choice about what happens when a write fails mid-session — don't block the user's whole study session on one failed write |
| 11 | **Design system / component composition** | `components/ui/{Button,Card,Badge,ProgressBar}.tsx` composed into feature components | Same principle as a component library in a large product — one place to change visual language |
| 12 | **Type-safe contracts across a network boundary** | `frontend/lib/types.ts` mirrors `backend/app/schemas/*.py` | The classic "backend and frontend drift out of sync" problem, addressed by treating the schema as a contract worth keeping in sync (and documented in `docs/API.md` as the source of truth) |
| 13 | **CI/CD pipeline design (fan-out by path)** | `.github/workflows/*.yml` triggered by `paths:` filters | Mirrors how larger orgs structure monorepo CI: don't run every check on every change |
| 14 | **Containerization and multi-stage builds** | `backend/Dockerfile` (single-stage, fine for a Python service) vs `frontend/Dockerfile` (multi-stage, strips build tooling from the runtime image) | Shows you know *why* multi-stage builds exist, not just that `FROM node` is a line you copy-paste |
| 15 | **Test pyramid** | Many fast pure-function unit tests (`test_scheduler.py`, `test_scoring.py`) + a few slower end-to-end integration tests through the real app (`test_reviews.py`) | Keeps the suite fast (12 tests run in ~0.5s) while still proving the full HTTP flow works, not just the math |

---

## Part 3 — How to navigate this repo to make a change

### The mental model

```
frontend/app/**/page.tsx   → what the user sees & does
frontend/lib/api.ts        → the only place that talks HTTP
backend/app/routers/*.py   → HTTP surface (thin)
backend/app/schemas/*.py   → the shape of data in/out
backend/app/services/*.py  → the actual logic/rules
backend/app/database.py    → how data is stored
```

Trace any feature top-to-bottom through those five stops, in that order.

### "I need to change X" — where to go

| Requirement | Start here |
|---|---|
| Change how something *looks* (colors, spacing, copy) | `frontend/components/**` or the relevant `frontend/app/**/page.tsx` |
| Add a new page/route | New folder under `frontend/app/`, e.g. `app/mnemonics/page.tsx`; add a nav link in `frontend/app/layout.tsx` |
| Change what data a page needs from the API | 1) `frontend/lib/types.ts` (add/edit the type) → 2) `frontend/lib/api.ts` (add/edit the call) → 3) the page/component that uses it |
| Add a new API endpoint | 1) `backend/app/schemas/*.py` (define request/response shape) → 2) `backend/app/routers/*.py` (add the route) → 3) register it in `backend/app/main.py` if it's a new router file → 4) write a test in `backend/tests/` |
| Change business rules (e.g. scheduling intervals, scoring logic) | `backend/app/services/*.py` **only** — routers should never contain this logic. Update/add a unit test in `backend/tests/` for the new behavior |
| Change what gets stored / the data model | `backend/app/schemas/*.py` for the shape, `docs/DATABASE.md` to keep the doc in sync, and check whether `services/analytics.py` needs to read the new field |
| Swap the database backend | One line: `USE_IN_MEMORY_DB=false` + `MONGO_URI=...` in `backend/app/config.py` / environment — no router or service code should need to change. If it does, that's a sign the abstraction leaked and `database.py` needs fixing |
| Add a new spaced-repetition strategy | `backend/app/services/scheduler.py` — keep it a pure function so it stays trivially testable, then wire it into `backend/app/routers/reviews.py` |

### A worked example: "add a `snooze` rating that pushes a question 3 days out"

1. **Schema** — add `snooze` to `ReviewRating` enum in `backend/app/schemas/review.py`.
2. **Logic** — add a `(3, 0.0)` entry to `_INTERVAL_LADDER` in `backend/app/services/scheduler.py`.
3. **Test** — add a `test_snooze_gives_three_day_interval` case in `backend/tests/test_scheduler.py`, run `pytest -v` to confirm it (and nothing else) changed.
4. **API contract** — no router change needed; `POST /api/reviews` already accepts any `ReviewRating`.
5. **Frontend type** — add `"snooze"` to the `ReviewRating` union in `frontend/lib/types.ts`.
6. **UI** — add a 5th button to `RATINGS` in `frontend/components/review/RatingButtons.tsx` (note: the grid is `grid-cols-4`, so bump it to `grid-cols-5`).
7. **Docs** — mention the new rating in `docs/API.md`.

That's the full loop: schema → logic → test → contract → UI → docs — the
same loop applies to almost any change in this codebase.
