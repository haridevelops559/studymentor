# Stack Deep-Dive — 75 Concepts Explored, Experimented, and Implemented

Format for every entry: **what it is → where it's implemented → the
production-grade edge case or trade-off → what it proves to an
interviewer.** This is written so a fresher can point at real code instead
of reciting definitions.

---

## A. React — 15 concepts

**1. Server Components vs. Client Components**
`app/dashboard/page.tsx` fetches data with `await api.dashboard.get()`
directly in an `async function` component — no `useState`/`useEffect`
needed, ships zero client JS for data-fetching. `app/review/page.tsx` is
marked `"use client"` because it needs interaction (`useState`, event
handlers). Edge case handled: forgetting `"use client"` on a component that
uses hooks fails at build time, not runtime — caught during `npm run build`.
*Proves:* you understand React 18's rendering model, not just "React runs
in the browser."

**2. Component composition over configuration**
`components/ui/Button.tsx` takes a `variant` prop (`primary/secondary/ghost`)
instead of every call site hardcoding classes. `Card`/`CardHeader` compose
rather than one monolithic `<DashboardCard title="" ... />` God-component.
*Proves:* you can design a small internal component API, the same skill
scaled up in any design-system job.

**3. Controlled inputs**
Every form (`NewSubjectForm.tsx`, `NewQuestionForm` in `practice/page.tsx`)
binds `value={state}` + `onChange` — React, not the DOM, owns the source
of truth. Edge case: the form clears itself (`setName("")`) only *after*
a successful API call, so a failed submit doesn't silently lose what the
user typed.

**4. Custom hooks encapsulating stateful logic**
`hooks/useDueQuestions.ts` hides fetch-on-mount, current-index tracking,
and the rate/advance flow behind one hook so `review/page.tsx` stays a
thin view. *Proves:* you know when logic belongs in a hook vs. inline in
a component — a core code-review skill.

**5. Loading / error / empty states as first-class UI states**
Every data-driven page renders three distinct branches: loading
(`isLoading`), error (`ApiError` caught and shown with actionable text,
not a stack trace), and empty (`questions.length === 0` → a specific
message, not a blank screen). See `dashboard/page.tsx`'s catch block
telling the user exactly which command starts the backend.

**6. Lists & keys**
`questions.map((q) => <li key={q._id}>...)` uses the database ID, never
the array index — the index-as-key anti-pattern would break state when a
question is deleted mid-list. `key={current._id}` on `<RetrievalCard>` in
`review/page.tsx` is deliberate: it forces React to *remount* the card
(resetting its internal `draftAnswer`/`revealed` state) every time the
question changes, instead of one card silently reusing stale state.

**7. Lifting state vs. keeping it local**
`RetrievalCard` owns its own `draftAnswer`/`revealed` state (nobody else
needs it) but calls `onRated(rating, givenAnswer)` to hand the *result* up
to the parent, which owns the session-level `attempted`/`correct` counts.
*Proves:* you know state should live at the lowest common ancestor that
actually needs it — not "lift everything" or "keep everything local."

**8. `useEffect` for data fetching, with a cancellation guard**
`useDueQuestions` sets a `let cancelled = false` flag and checks it before
calling `setState` in the `.then()`/`.catch()` — this is the real-world
fix for "Can't perform a React state update on an unmounted component"
when a user navigates away mid-fetch.

**9. `useCallback` for referential stability**
`rate` in `useDueQuestions.ts` is wrapped in `useCallback` with
`[questions, index]` as deps, so consumers get a stable function reference
across renders instead of a new closure every render — relevant the moment
this hook's return value is passed into a memoized child.

**10. Derived state instead of duplicated state**
`isComplete` in `useDueQuestions` is computed (`!isLoading && index >=
questions.length`), not stored in its own `useState`. Avoids a whole class
of bugs where two pieces of state disagree after a partial update.

**11. Prop-driven variants for reusable primitives**
`RatingButtons.tsx` maps over a `RATINGS` config array instead of four
hand-written `<button>` elements — adding a 5th rating (e.g. `snooze`) is
a one-line config change, not a copy-pasted block.

**12. `Suspense` boundaries around `useSearchParams`**
Next.js requires any component using `useSearchParams()` to be wrapped in
`<Suspense>` for the build to succeed — `review/page.tsx`,
`practice/page.tsx`, and `feynman/page.tsx` all split into an outer
`Suspense`-wrapped default export and an inner `...Content()` component.
This is a real Next.js build-time constraint you'd only learn by hitting
the build error.

**13. Reading navigation state (`useSearchParams`)**
`subject`/`topic` filters flow through the URL (`?subject=...`) rather
than component state, so a link like `/practice?subject=abc` is
shareable/bookmarkable and survives a page refresh — a deliberate choice
over `useState` for anything that should be part of the URL.

**14. Event handling & synthetic form submission**
Every form calls `event.preventDefault()` before its async submit logic —
missing this is one of the most common fresher bugs (page reloads, state
resets, network tab shows a full navigation instead of a fetch).

**15. Avoiding unnecessary re-renders via structural keys**
Combined with #6: using `key={current._id}` is also a *performance*
decision, not just correctness — it tells React exactly which subtree can
be thrown away and rebuilt rather than diffed field-by-field.

---

## B. TypeScript & Next.js — 15 concepts

**1. App Router file-based routing**
`app/dashboard/page.tsx` → `/dashboard`, `app/subjects/page.tsx` →
`/subjects`, with no route config file anywhere — the folder structure
*is* the routing table. Adding a page is "add a folder," not "register a
route."

**2. Shared type contracts across a network boundary**
`frontend/lib/types.ts` mirrors `backend/app/schemas/*.py` field-for-field.
Edge case flagged in `docs/API.md`: these can drift, so the backend schema
is documented as the source of truth and any schema change should update
both.

**3. String-literal unions over `enum`**
`ReviewRating = "again" | "hard" | "good" | "easy"` instead of a TS
`enum`. Deliberate: literal unions serialize identically to the JSON the
Python `Enum` sends over the wire, with no runtime object needed on the
frontend — fewer footguns at a network boundary.

**4. Generic, type-inferring API helper**
`request<T>(path, options): Promise<T>` in `lib/api.ts` lets every call
site (`api.subjects.list(): Promise<Subject[]>`) get full autocomplete and
compile-time errors if a caller expects the wrong shape — one generic
function instead of duplicating fetch logic per endpoint.

**5. Strict mode & null-safety**
`tsconfig.json` has `"strict": true`. Concretely this caught real bugs
while building: `Note.summary` and `Question.last_reviewed` are typed
`string | null`, forcing every consumer to handle the null case instead of
assuming a value exists.

**6. Path aliases (`@/*`)**
`baseUrl: "."` + `paths: { "@/*": ["./*"] }` in `tsconfig.json` means
`import { api } from "@/lib/api"` instead of `../../../lib/api` —
directly relevant once folders nest (as they do here: `app/review/page.tsx`
importing from `components/review/`).

**7. Typed, prefixed environment variables**
`NEXT_PUBLIC_API_URL` — the `NEXT_PUBLIC_` prefix is a real Next.js rule
(anything without it is server-only and won't reach the browser bundle).
Getting this wrong is a classic "why is my env var `undefined` in the
browser" fresher bug, deliberately avoided in `lib/api.ts`.

**8. The Metadata API**
`export const metadata: Metadata = { title, description }` in
`app/layout.tsx` — Next.js's typed replacement for manually writing
`<head>` tags, with autocomplete for every valid meta field.

**9. Explicit rendering mode control**
`export const dynamic = "force-dynamic"` on `subjects/page.tsx` — without
it, Next.js might statically prerender a page whose content should be
fresh on every request (subjects are created/mutated constantly).
Understanding *why* you need this, not just copy-pasting it, is the actual
skill.

**10. Async Server Components as a data-fetching pattern**
`export default async function DashboardPage()` — the component function
itself is `async` and can `await` directly, no `useEffect` needed. This is
specific to Server Components and doesn't work in a `"use client"` file —
worth being able to explain the boundary precisely.

**11. Try/catch as the Server Component error strategy**
`dashboard/page.tsx` wraps its fetch in try/catch and renders a fallback
UI in the catch block, rather than letting the fetch throw into a generic
Next.js error page — a deliberate choice to give the user an actionable
message ("start the backend with...") instead of a stack trace.

**12. Type narrowing with `instanceof`**
`error instanceof ApiError ? error.message : "generic fallback"` — used
consistently across every page's catch block so TypeScript narrows
`error` (typed `unknown` in a catch clause under strict mode) into the
custom class before accessing `.message`.

**13. Discriminated response shapes**
`DashboardResponse.due` is a nested object (`{overdue, due_today,
upcoming}`) typed explicitly rather than `Record<string, number>`, so
`TodayPlan.tsx` gets autocomplete and a compile error if a field is
renamed on the backend.

**14. Module resolution & the build as a type-checking CI gate**
`npm run build` runs full type-checking, not just bundling — this is
literally how the two real bugs earlier (`let subjects` untyped,
unescaped apostrophe) were caught before ever reaching a person. In CI
(`frontend-ci.yml`), this is the gate that blocks a bad PR from merging.

**15. Environment-based config with sane defaults**
`API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api"`
— the app works with zero `.env` setup for local dev, but is fully
configurable for staging/prod via one variable. `.env.example` documents
the contract without committing real secrets.

---

## C. Tailwind CSS — 15 concepts

**1. Utility-first over hand-written CSS files**
Zero `.css` files besides `globals.css` (which itself is mostly
`@tailwind` directives) — every visual decision lives next to the markup
that needs it, which is the actual argument for utility-first: no
context-switching between a component file and a stylesheet.

**2. Design tokens via `theme.extend`**
`tailwind.config.ts` defines a custom `brand` color scale (50–900) and a
domain-specific `recall` scale (`again/hard/good/easy`) instead of reaching
for Tailwind's default `red-500`/`blue-500` inline everywhere. Changing the
brand color is a one-file edit, not a find-and-replace across 20 components.

**3. Responsive design with breakpoint prefixes**
`grid grid-cols-2 sm:grid-cols-4` in `StatsGrid.tsx` — 2 columns on mobile,
4 on larger screens, with no media-query CSS written by hand. Tested by
resizing the browser during development, the actual "experimentation" part.

**4. Component classes via `@layer components`**
`.card`, `.stat-tile`, `.pill` are defined once in `globals.css` under
`@layer components` and reused everywhere (`className="card"`) instead of
repeating `rounded-2xl border border-slate-200 bg-white p-5 shadow-card`
in 15 different files — the DRY line between "utility-first" and
"maintainable."

**5. State variants (`hover:`, `focus-visible:`, `disabled:`)**
`Button.tsx`: `hover:bg-brand-700 focus-visible:outline-brand-600
disabled:cursor-not-allowed disabled:opacity-50`. The `focus-visible:`
(not just `focus:`) choice is deliberate — it shows keyboard focus rings
only for keyboard users, not on every mouse click, an actual accessibility
distinction.

**6. Conditional/dynamic class composition**
`lib/utils.ts: cn(...)` filters out falsy class strings — used everywhere
a class list depends on state, e.g. the active-topic pill in
`practice/page.tsx`:
`selectedTopicId === topic._id ? "bg-brand-600 text-white" : "bg-white ..."`.

**7. A consistent spacing scale**
Every gap/padding value (`gap-3`, `p-5`, `py-2.5`) comes from Tailwind's
default 4px-based scale — never an arbitrary `p-[13px]` — which is what
keeps a UI feeling aligned without a design tool, purely from consistent
token usage.

**8. Domain-meaningful color semantics**
The `recall` palette isn't decorative — `recall-again` (red) vs
`recall-easy` (blue) directly encodes the spaced-repetition rating scale
in `RatingButtons.tsx`, so the color *is* the information, not just theme.

**9. Accessible focus states as a non-negotiable**
Every interactive element (`Button`, form inputs) has a visible
`focus-visible:outline` — checked deliberately rather than left to
browser defaults, since Tailwind's reset removes the default outline and
it's easy to forget to add one back.

**10. Grid vs. Flexbox, chosen per layout shape**
`StatsGrid` uses `grid` (fixed-count tiles); `NewSubjectForm` uses `flex`
(a form row that should just flow). Choosing the right primitive per shape,
not defaulting to one everywhere, is itself a small but real skill.

**11. Sticking to the theme scale instead of arbitrary values**
Almost no `[...]` arbitrary-value syntax appears in the codebase — colors,
spacing, and radii all come from the configured scale, which keeps the
whole UI visually consistent and keeps the generated CSS small.

**12. The PostCSS/Autoprefixer pipeline**
`postcss.config.js` wires `tailwindcss` + `autoprefixer` — understanding
that Tailwind itself is a PostCSS plugin (not a standalone compiler) is
the kind of detail that separates "I used Tailwind" from "I understand the
build pipeline it sits in."

**13. `content` globs and production bundle size**
`tailwind.config.ts: content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"]`
— Tailwind scans exactly these files to decide which utility classes to
keep; anything outside these globs (accidentally) would get its classes
purged in production, a real "why did my styles disappear in the build"
debugging scenario.

**14. Transitions as intentional, restrained motion**
`transition`, `transition-all` appear only on interactive elements
(buttons, progress bars) — not globally — following the frontend-design
principle of using motion deliberately rather than decorating everything.

**15. Building a small design system without a component library**
Colors (`brand`, `recall`), spacing scale, and reusable component classes
together form a lightweight design system defined entirely in
`tailwind.config.ts` + `globals.css` — the same conceptual exercise as
adopting a full design-token system at a larger company, at MVP scale.

---

## D. FastAPI & Pydantic — 15 concepts

**1. Modular routers over one giant file**
`APIRouter(prefix="/subjects", tags=["subjects"])` per domain
(`subjects.py`, `questions.py`, `reviews.py`, ...), all mounted in
`main.py` with `app.include_router(...)`. Mirrors how a real production
FastAPI service is organized — one file per resource, not a 2,000-line
`main.py`.

**2. Pydantic models as the validation layer**
`QuestionCreate(BaseModel)` with `Field(..., min_length=1)` means an empty
`question` string is rejected with a `422` *before* any handler code runs
— validation lives in the schema, not scattered `if` checks in route
functions.

**3. `response_model` controlling exactly what leaves the API**
`@router.post("", response_model=Question)` — even if a handler
accidentally returns extra internal fields, Pydantic filters the response
down to the declared model. A real security-relevant habit (never leak
more than you meant to).

**4. Field constraints as real input validation, tested**
`min_length=1` on note content, `max_length=2000` on `given_answer` in
`ReviewCreate` — these aren't decorative; an empty note or a runaway
10,000-character answer is rejected at the boundary, not deep in business
logic.

**5. `Enum`-backed fields for closed value sets**
`ReviewRating(str, Enum)` and `QuestionType(str, Enum)` — a request with
`"rating": "excellent"` (not one of the four valid values) is rejected
automatically by Pydantic with a clear error, instead of silently being
stored as garbage.

**6. Schema inheritance to avoid duplication**
`Question(QuestionCreate)` — the "create" shape is the base, and the
full stored/returned shape extends it with server-owned fields
(`next_review`, `review_count`, ...). One source of truth for the shared
fields instead of two independently-maintained schemas drifting apart.

**7. `default_factory` for correct-at-call-time defaults**
`created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))`
— using a factory instead of a bare default avoids the classic Python
bug where a *mutable/eagerly-evaluated* default is computed once at
import time and shared across every instance.

**8. Centralized, typed settings via `pydantic-settings`**
`class Settings(BaseSettings)` in `config.py` reads from environment
variables / `.env` with real types (`bool`, `list[str]`) and validation,
instead of scattering `os.getenv("SOME_VAR", "default")` calls throughout
the codebase.

**9. A lightweight dependency-injection pattern**
`get_collection(name)` is called directly rather than using FastAPI's
`Depends()` — a deliberate simplification for this size of project, but
one worth being able to justify: at a larger scale, this would become an
injected dependency for easier test overrides.

**10. `async def` handlers for I/O-bound work**
Every route is `async def`, and every database call is `await`ed — this
matters even against the in-memory store (so swapping to real async Mongo
I/O via Motor requires no handler changes) and is the correct default for
any I/O-bound API regardless of backend.

**11. `HTTPException` for explicit, typed error responses**
`raise HTTPException(status_code=404, detail="Question not found")` in
`reviews.py` when a review references a question that doesn't exist —
tested explicitly in `test_review_for_missing_question_returns_404`. This
is the difference between an API that fails loudly and correctly vs. one
that 500s on bad input.

**12. CORS as explicit, environment-driven config**
`CORSMiddleware(allow_origins=settings.cors_origins)` — origins come from
settings, not hardcoded `"*"`, so a production deploy can restrict exactly
which frontend domains may call the API.

**13. Free, always-in-sync API docs**
FastAPI auto-generates OpenAPI/Swagger docs at `/docs` directly from the
Pydantic models and route signatures — zero hand-maintained API
documentation to go stale, verified just by running the server and
opening `/docs`.

**14. Field aliasing for `_id` vs `id`**
`id: str = Field(alias="_id")` with `model_config = {"populate_by_name":
True}` — bridges MongoDB's `_id` convention with a cleaner Python-facing
`id`/frontend-facing `_id` contract without hand-writing conversion code
in every route.

**15. In-process integration testing with `httpx.ASGITransport`**
`test_reviews.py` drives the *real* FastAPI app (routing, validation,
database) through `AsyncClient(transport=ASGITransport(app=app))` — no
real network socket, no separate server process, but a genuinely full
request/response cycle. This is the modern, correct way to integration-test
an ASGI app, not `TestClient` from years-old tutorials.

---

## E. MongoDB / Database design — 15 concepts

**1. Document design: reference over embed, deliberately**
Topics reference `subject_id`, questions reference `topic_id`, reviews
reference `question_id` — normalized references rather than embedding
(e.g. questions nested inside topic documents). Reasoning to state
out loud: questions are queried and updated independently far more often
than topics are, so embedding would force rewriting a whole topic document
on every single review.

**2. Collections matching access patterns, not just "entities"**
`reviews` is a separate append-only collection from `questions` even
though a review always relates to exactly one question — because "list
all reviews today" and "get the current state of a question" are
different query shapes with different growth rates (reviews grow forever;
questions don't).

**3. Indexing strategy for the actual hot query**
`docs/DATABASE.md` calls out a compound index on `questions(topic_id,
next_review)` specifically because `GET /questions/due` filters and
implicitly sorts by exactly those two fields — an index chosen from the
query, not guessed at.

**4. Async driver usage (Motor) as the production path**
`MotorCollectionAdapter` wraps `AsyncIOMotorClient` — using the async
driver (not `pymongo`'s sync client) inside an `async def` FastAPI handler
is required to avoid blocking the event loop; using the sync driver here
would silently serialize all requests under load.

**5. `_id` handling and type conversion at the boundary**
`MotorCollectionAdapter.insert_one` converts Mongo's `ObjectId` to `str`
immediately (`doc["_id"] = str(result.inserted_id)`) so the rest of the
app — and the JSON API — never has to special-case `ObjectId`
serialization, a very common real-world FastAPI+Mongo gotcha.

**6. Storage abstraction / adapter pattern for testability**
The entire point of `InMemoryCollection` mirroring the same interface as
`MotorCollectionAdapter`: tests run against real business logic with zero
network calls and zero Docker dependency, while production runs the exact
same routers against real Mongo — proven by the fact that switching is one
config flag, not a code change.

**7. Denormalization as a conscious trade-off**
`review_count`/`correct_count`/`difficulty` are stored directly on the
`questions` document rather than recomputed from the `reviews` collection
on every read. Trade-off named explicitly: faster reads (no aggregation
needed for `/questions/due`), at the cost of needing to keep the counters
in sync on every write (`reviews.py: submit_review` updates both
collections in the same request).

**8. Query filtering via structured dict queries**
`get_collection("questions").find({"topic_id": topic_id})` — parameterized
queries, never string-built ones, which is also what prevents NoSQL
injection: query shape is always a Python dict built from typed Pydantic
fields, never raw string concatenation from user input.

**9. Aggregation done in the app layer vs. a Mongo aggregation pipeline**
`services/analytics.py` computes retention/due-counts in Python after
fetching documents, rather than a MongoDB `$group`/`$bucket` aggregation
pipeline. Named trade-off: simpler to read and unit-test without a
database at all (see `test_scheduler.py`-style pure-function tests), but
doesn't scale to millions of documents — the documented next step if data
volume grows is moving this into a real aggregation pipeline.

**10. Multi-document consistency without transactions (an honest gap)**
`submit_review` writes to *two* collections (`questions` update +
`reviews` insert) as two separate operations, not inside a Mongo
multi-document transaction. Explicitly flagged as an MVP limitation: if
the process crashes between the two writes, they can go out of sync — a
production version would wrap this in a `session.with_transaction()`
block. Naming this gap unprompted is exactly the kind of thing that reads
as senior-minded, not a weakness to hide.

**11. Schema evolution without a formal migration system**
No migration tool is used yet (fine for an MVP with no production data),
but this is flagged in `docs/DATABASE.md` as a known scope boundary —
adding a required field to an existing collection later would need a
backfill script, since MongoDB won't enforce schema retroactively.

**12. TTL / data growth considerations for append-only collections**
`reviews` and `study_sessions` grow forever by design (that's the whole
point — review history). Noted as a forward-looking concern: a real
deployment would eventually need either a TTL index on old review rows or
a periodic archival job, not addressed in v1 but worth naming as "known
next step" in an interview.

**13. Connection lifecycle: a singleton client, not one-per-request**
`_motor_client`/`_motor_db` in `database.py` are created once (module-level
globals, lazily initialized) and reused across every request — creating a
new `AsyncIOMotorClient` per request would exhaust connections under load;
Motor's client is designed to be created once and reused for the app's
lifetime.

**14. Test isolation without a real database**
`tests/conftest.py`'s `reset_in_memory_db()` fixture wipes all in-memory
collections before/after every test — the NoSQL equivalent of a rolled-back
transaction in a SQL test suite, achieved without needing a MongoDB test
container or `mongomock` dependency.

**15. Read/write shape driving the API design, not the other way around**
The whole `/dashboard` endpoint exists because the *read pattern* (show me
everything about today, all at once) doesn't match any single collection's
natural shape — it's a deliberate example of designing an endpoint around
how data will actually be consumed, not just exposing raw CRUD over each
collection.

---

## How to use this document in an interview

Don't recite this list. Pick 2–3 items per section that you can actually
open the file for and narrate live: *"here's the trade-off, here's the
test that proves it, here's what I'd change at 10x scale."* That's the
difference recruiters are listening for between a fresher who used a
tutorial's stack and one who reasoned through it.
