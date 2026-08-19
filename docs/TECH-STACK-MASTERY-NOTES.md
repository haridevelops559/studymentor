# Tech-Stack Mastery Notes — Production-Grade, Recruiter-Facing

Format per concept: **What it is** → **Edge case / production concern** →
**Where in this repo** → **Recruiter-proof line** (the sentence you'd
actually say in an interview).

---

## 1. React — 15 concepts

**1. Server Components vs Client Components**
Next.js App Router defaults every component to a Server Component; `"use client"` opts in to the browser runtime.
Edge case: putting `useState` in a Server Component fails at build time — you must draw the boundary deliberately.
Repo: `app/dashboard/page.tsx` (server) vs `app/review/page.tsx` (client).
*"I split rendering by data-vs-interactivity, not by habit — dashboard fetches on the server, review needs client state for the retrieval loop."*

**2. Component composition over configuration**
Small, single-purpose components (`Button`, `Card`, `Badge`) composed into feature UI instead of one giant configurable component.
Edge case: over-composing creates prop-drilling; the fix is colocating state near where it's used.
Repo: `components/ui/*` composed inside `components/dashboard/*`.
*"I built a small internal design system rather than repeating className strings everywhere."*

**3. Controlled inputs and form state**
Every input in the app (`NewSubjectForm`, `RetrievalCard`) is a controlled component — value comes from state, `onChange` updates it.
Edge case: uncontrolled inputs mixed with controlled ones cause React warnings and lost keystrokes on rerender.
Repo: `components/notes/NewSubjectForm.tsx`.
*"I kept form state controlled end-to-end so validation and reset logic stay predictable."*

**4. `useState` for local UI state, lifted only when shared**
`RetrievalCard` owns its own `revealed`/`draftAnswer` state; it doesn't leak into a parent unless the parent needs it.
Edge case: over-lifting state causes unnecessary rerenders of unrelated siblings.
Repo: `components/review/RetrievalCard.tsx`.
*"I only lift state when two components actually need to share it — otherwise it stays local."*

**5. `useEffect` for synchronizing with an external system (the API)**
`useDueQuestions` fetches on mount and re-fetches when `topicId` changes, with a `cancelled` flag to avoid setting state after unmount.
Edge case: forgetting the cleanup flag causes a "set state on unmounted component" warning/race if the user navigates away mid-fetch.
Repo: `hooks/useDueQuestions.ts`.
*"I guard every effect-based fetch against the component unmounting before the request resolves."*

**6. Custom hooks to extract reusable stateful logic**
`useDueQuestions` bundles fetch + index + score tracking into one hook so the page component stays about rendering, not data plumbing.
Edge case: a custom hook that returns too many loosely-related values becomes as hard to read as inline logic — keep it single-purpose.
Repo: `hooks/useDueQuestions.ts`.
*"I extracted the review-session state machine into a hook so I could reason about it independently of JSX."*

**7. Keys and list identity**
`RetrievalCard key={current._id}` forces React to remount the component (resetting `draftAnswer`/`revealed`) when the question changes, instead of reusing the same instance with stale state.
Edge case: using array index as a key here would leave old answers visible on the next question.
Repo: `app/review/page.tsx`.
*"I used the question ID as a key specifically to force a clean remount between questions — an index key would have leaked state."*

**8. Conditional rendering as a state machine (loading / error / empty / success)**
Every data-driven page explicitly renders four distinct states rather than assuming success.
Edge case: skipping the empty state silently shows a blank page that looks broken.
Repo: `app/review/page.tsx`, `app/dashboard/page.tsx`.
*"I treat loading/error/empty/success as a real state machine, not an afterthought bolted on with a ternary."*

**9. Composition via children/props instead of inheritance**
`CardHeader` takes a `title` + optional `action` node rather than being subclassed.
Edge case: React has no class inheritance model for components — trying to force it leads to awkward code.
Repo: `components/ui/Card.tsx`.
*"React favors composition; I pass an `action` slot into `CardHeader` instead of trying to inherit/override it."*

**10. Derived state instead of duplicated state**
`isComplete` in `useDueQuestions` is computed from `index >= questions.length`, not stored as its own `useState`.
Edge case: storing it separately would require remembering to update it everywhere `index` changes — a classic source of state bugs.
Repo: `hooks/useDueQuestions.ts`.
*"I compute values from existing state rather than storing redundant state that can drift out of sync."*

**11. Event handler naming convention (`onX` prop, `handleX` implementation)**
`onRated`, `onCreated` as props; `handleSubmit` as the internal implementation.
Edge case: inconsistent naming makes it hard to tell at a glance which functions are props vs local handlers.
Repo: `components/review/RetrievalCard.tsx`, `components/notes/NewSubjectForm.tsx`.
*"I keep a consistent on/handle naming convention so prop callbacks are visually distinct from internal handlers."*

**12. Optimistic-vs-pessimistic UI trade-off**
The review flow advances to the next question only after the server call settles (pessimistic), but still advances on error so one failed write doesn't block the whole session.
Edge case: true optimistic UI would need a rollback path if the server rejects — deliberately avoided here for simplicity.
Repo: `hooks/useDueQuestions.ts: rate()`.
*"I chose pessimistic updates with graceful error handling over optimistic UI, because reverting a `rating` on failure adds complexity I judged wasn't worth it for a study app."*

**13. `Suspense` boundaries around `useSearchParams`**
Next.js requires client components reading `useSearchParams()` to be wrapped in `<Suspense>` or the build fails/hydration mismatches.
Edge case: forgetting this boundary is a common Next.js App Router gotcha that only surfaces at build time.
Repo: `app/review/page.tsx`, `app/practice/page.tsx`, `app/feynman/page.tsx`.
*"I ran into the Suspense-around-useSearchParams requirement during `next build` and fixed it rather than suppressing the error."*

**14. Avoiding prop drilling with focused component boundaries**
Instead of passing `topicId` through five layers, each page reads it once from the URL and passes only what a child actually needs.
Edge case: naive prop drilling makes refactors expensive because every intermediate component must be touched.
Repo: `app/practice/page.tsx` passes `topicId` directly to `NewQuestionForm`, not through intermediate wrappers.
*"I kept the component tree shallow enough that I didn't need Context for this app's scale — I'd reach for Context or a store only if drilling got past 2–3 levels."*

**15. Accessibility basics: labels, `aria-hidden` on decorative content**
Form inputs paired with `<label>`, emoji icons marked `aria-hidden` since they're decorative, not informational.
Edge case: skipping `aria-hidden` on emoji makes screen readers announce "face with cold sweat" mid-sentence.
Repo: `components/review/RatingButtons.tsx`.
*"I mark decorative icons aria-hidden so screen readers don't announce emoji names — small thing, but it's the kind of detail production teams check for."*

---

## 2. TypeScript / Next.js — 15 concepts

**1. Shared type contract across frontend and backend**
`lib/types.ts` mirrors `backend/app/schemas/*.py` by hand.
Edge case: schemas drift silently if not kept in sync — mitigated by treating `docs/API.md` as the documented source of truth.
Repo: `frontend/lib/types.ts`.
*"I know hand-mirrored types don't scale past a certain team size — the next step would be OpenAPI codegen (`openapi-typescript`) directly from FastAPI's schema."*

**2. Discriminated unions for finite state (`ReviewRating`)**
`type ReviewRating = "again" | "hard" | "good" | "easy"` — a string literal union, not a loose `string`.
Edge case: without this, a typo like `"gud"` would compile fine and fail silently at runtime.
Repo: `frontend/lib/types.ts`.
*"I use string literal unions for anything with a fixed set of values so the compiler catches typos I'd otherwise only see in production."*

**3. Generics in the API client**
`request<T>(path, options)` is generic over the response shape, so every `api.*` call returns a fully-typed result without casting.
Edge case: without generics, every call site would need an `as Question[]` cast — easy to get wrong and lose type safety.
Repo: `frontend/lib/api.ts`.
*"I wrote one generic `request<T>` helper instead of duplicating fetch logic per endpoint, and generics keep every call typed without manual casts."*

**4. Custom error class (`ApiError extends Error`)**
Carries a `.status` field so callers can branch on 404 vs 500 vs network failure.
Edge case: throwing a raw string or plain object loses the stack trace and `instanceof` narrowing.
Repo: `frontend/lib/api.ts`.
*"I extended `Error` rather than throwing a plain object so `instanceof ApiError` narrowing works throughout the app."*

**5. Strict mode and null-safety (`strict: true` in tsconfig)**
Forces explicit handling of `Optional`/nullable fields like `Note.summary?: string | null`.
Edge case: without strict mode, accessing a possibly-null field compiles fine and crashes at runtime.
Repo: `frontend/tsconfig.json`, reflected in `frontend/lib/types.ts`'s liberal use of `?:` and `| null`.
*"I turned on strict mode from day one — retrofitting it onto an existing codebase is far more painful than starting with it."*

**6. App Router file-based routing conventions**
`app/dashboard/page.tsx` → `/dashboard`; `app/subjects/page.tsx` → `/subjects`. No manual route config.
Edge case: a `page.tsx` inside a folder without one is simply not a route — a common source of "why isn't this rendering" confusion for React Router migrants.
Repo: `frontend/app/*`.
*"I used the App Router's file-based convention rather than Pages Router, which also unlocked Server Components."*

**7. `dynamic = "force-dynamic"` vs static generation**
Explicitly opt a page out of static generation when it must always reflect live server state (subjects list).
Edge case: without this, Next.js may statically cache the page at build time, showing stale data to every visitor.
Repo: `frontend/app/subjects/page.tsx`.
*"I explicitly marked pages that read live server state as dynamic rather than relying on Next.js's default caching heuristics."*

**8. Environment variables and the `NEXT_PUBLIC_` prefix**
Only variables prefixed `NEXT_PUBLIC_` are exposed to the browser bundle; everything else stays server-only.
Edge case: accidentally prefixing a secret with `NEXT_PUBLIC_` ships it to every client — a real security footgun.
Repo: `frontend/.env.example`, `frontend/lib/api.ts: process.env.NEXT_PUBLIC_API_URL`.
*"I know the `NEXT_PUBLIC_` prefix is a security boundary, not just a naming convention — anything without it never reaches client JS."*

**9. Path aliases (`@/*`) for import ergonomics**
`tsconfig.json`'s `paths` maps `@/lib/api` to `./lib/api` regardless of file depth.
Edge case: without this, deeply nested components accumulate `../../../lib/api` imports that break on file moves.
Repo: `frontend/tsconfig.json`, used throughout `frontend/components/**`.
*"I set up a path alias early so refactors that move files don't cascade into broken relative imports."*

**10. Build-time type checking as a CI gate**
`next build` runs the TypeScript compiler and ESLint; a type error fails the build, not just a warning.
Edge case: `next dev` is more forgiving than `next build` — I caught a real type error (`let subjects` with no inferred type across a try/catch) only at build time.
Repo: `.github/workflows/frontend-ci.yml: npm run build`.
*"I treat `next build` passing as a hard CI gate, not optional — it caught a real inference bug that `next dev` didn't."*

**11. Interfaces vs type aliases, used consistently**
`interface` for object shapes meant to be extended (`Subject`, `Question`), `type` for unions (`ReviewRating`, `QuestionType`).
Edge case: mixing both arbitrarily doesn't break anything technically, but makes a codebase harder to scan.
Repo: `frontend/lib/types.ts`.
*"I follow one convention — interfaces for extensible object shapes, type aliases for unions — so the codebase reads consistently."*

**12. Metadata API for SEO/head management**
`export const metadata: Metadata = {...}` in `layout.tsx` instead of a manual `<Head>` component.
Edge case: the old `next/head` pattern doesn't work the same way in the App Router — this is the replacement.
Repo: `frontend/app/layout.tsx`.
*"I used the App Router's typed Metadata API rather than the Pages Router's `next/head` pattern."*

**13. Async Server Components awaiting data directly**
`export default async function DashboardPage()` — no `useEffect`, no loading state needed; the `await` happens during render on the server.
Edge case: you cannot do this in a Client Component — this is one of the concrete reasons to keep something server-side.
Repo: `frontend/app/dashboard/page.tsx`.
*"This is the concrete benefit of Server Components I can point to — no client-side fetch waterfall for the dashboard."*

**14. Module boundaries: `lib/` (pure logic) vs `components/` (UI) vs `hooks/` (stateful logic)**
A strict rule: `lib/` never imports React; `hooks/` never renders JSX; `components/` never contains raw `fetch`.
Edge case: violating this (e.g., a `fetch` inside a component) makes logic untestable without a DOM.
Repo: `frontend/lib/*`, `frontend/hooks/*`, `frontend/components/*`.
*"I enforce a boundary where business/network logic never lives directly inside a component — that's what makes `lib/api.ts` swappable or unit-testable later."*

**15. Type narrowing via `instanceof` in catch blocks**
`catch (error) { const message = error instanceof ApiError ? error.message : "..." }` — TypeScript's control-flow analysis narrows `error`'s type inside the `if`.
Edge case: `catch` clauses type `error` as `unknown` in strict TS — you cannot access `.message` without narrowing first.
Repo: `frontend/app/dashboard/page.tsx`.
*"I narrow caught errors with `instanceof` rather than casting to `any`, which strict mode would otherwise tempt you to do."*

---

## 3. Tailwind CSS — 15 concepts

**1. Utility-first over custom CSS files**
No `.css` files beyond `globals.css`; all styling is inline utility classes.
Edge case: without discipline this becomes unreadable — mitigated by extracting repeated utility groups into `@layer components` classes.
Repo: `frontend/app/globals.css: .card, .stat-tile, .pill`.
*"I extracted the 2–3 utility combinations that repeated everywhere into named component classes via `@layer components`, rather than letting `className` strings sprawl."*

**2. Custom design tokens in `tailwind.config.ts`**
Added a `brand` color scale and a domain-specific `recall` scale (`again/hard/good/easy`) instead of using Tailwind's defaults inline.
Edge case: hardcoding `text-red-500` in five different files means a rebrand touches five files instead of one config.
Repo: `frontend/tailwind.config.ts`.
*"I modeled the recall-rating colors as design tokens, not inline hex/utility classes, so the whole rating color language lives in one file."*

**3. `content` config and unused-CSS purging**
`content: ["./app/**/*.{tsx}", "./components/**/*.{tsx}"]` tells Tailwind exactly which files to scan so unused utilities are purged from the production bundle.
Edge case: a class built via string concatenation (e.g. `` `bg-${color}-500` ``) won't be detected by the scanner and gets purged — I avoided this pattern deliberately.
Repo: `frontend/tailwind.config.ts`, avoided in `frontend/lib/utils.ts: retentionColor()` which returns full static class names, not concatenated ones.
*"I return complete static class strings from helper functions like `retentionColor()` specifically because Tailwind's purge step can't see dynamically-concatenated class names."*

**4. Responsive design with breakpoint prefixes**
`grid-cols-2 sm:grid-cols-4` in the stats grid — mobile-first, then widened at the `sm` breakpoint.
Edge case: forgetting mobile-first ordering (writing `sm:grid-cols-2 grid-cols-4` conceptually backwards) doesn't error, but produces confusing intent.
Repo: `frontend/components/dashboard/StatsGrid.tsx`.
*"I write mobile styles unprefixed and desktop as `sm:`/`md:` overrides, which is Tailwind's intended mobile-first mental model."*

**5. State variants (`hover:`, `focus-visible:`, `disabled:`)**
Buttons define hover, keyboard-focus, and disabled states entirely through Tailwind variants, no separate CSS or JS-driven className toggling.
Edge case: using `focus:` instead of `focus-visible:` shows focus rings on mouse clicks too, which most designers consider visual noise.
Repo: `frontend/components/ui/Button.tsx`.
*"I used `focus-visible:` specifically instead of `focus:` so focus rings only appear for keyboard users, not mouse clicks."*

**6. Conditional className composition with a `cn()` helper**
A small utility (`cn(...classes: (string|false|null|undefined)[])`) filters falsy values so conditional classes read cleanly.
Edge case: without it, `` `base ${isActive && "active"}` `` can literally inject the string `"false"` into the DOM class list when `isActive` is false.
Repo: `frontend/lib/utils.ts: cn()`, used in `frontend/components/ui/Button.tsx`.
*"I wrote a tiny `cn()` helper — the same pattern as `clsx` — specifically to avoid the 'literal false in className' bug."*

**7. Component-scoped variant maps instead of ternary chains**
`VARIANT_CLASSES: Record<Variant, string>` in `Button.tsx` maps a typed variant prop to a class string, rather than nested ternaries.
Edge case: ternary chains for 3+ variants become unreadable and are easy to get an `else` branch wrong in.
Repo: `frontend/components/ui/Button.tsx`.
*"I map variants through a typed `Record`, which also means TypeScript will error if I add a new `Variant` and forget its class mapping."*

**8. Arbitrary values used sparingly, not as a first resort**
No arbitrary-value classes (`w-[123px]`) appear in the base UI components — everything sits on Tailwind's spacing/sizing scale.
Edge case: overusing arbitrary values defeats the purpose of a design system, since values stop being reusable/consistent.
Repo: `frontend/components/ui/*`.
*"I stayed on Tailwind's default spacing scale everywhere instead of reaching for arbitrary pixel values — consistency over pixel-perfection."*

**9. Semantic color usage vs literal color names**
The `recall` token names describe *meaning* (`again`, `good`) not literal colors (`red`, `green`), so swapping the palette later doesn't require renaming every usage.
Edge case: naming a token `red-warning` instead of `error` couples the design intent to a specific hue.
Repo: `frontend/tailwind.config.ts: colors.recall`.
*"I name design tokens by meaning, not by color, so a future rebrand or dark-mode palette swap doesn't require touching every component."*

**10. Transitions and micro-interactions as utilities**
`transition`, `hover:bg-brand-700` on buttons — no custom `@keyframes`, no JS animation library for simple state changes.
Edge case: relying on a JS animation library for something this simple adds bundle size for no benefit.
Repo: `frontend/components/ui/Button.tsx`.
*"For simple hover/focus transitions I lean on Tailwind's `transition` utilities rather than pulling in a JS animation library — that's a bundle-size decision, not just a styling one."*

**11. Consistent spacing rhythm via a shared scale**
`gap-3`, `gap-4`, `gap-6`, `space-y-6` chosen from Tailwind's default scale rather than one-off values, giving the whole app a consistent visual rhythm.
Edge case: inconsistent spacing across pages is one of the most common visual QA issues in Tailwind codebases without discipline.
Repo: consistent across `frontend/app/**/page.tsx`.
*"I standardized on `space-y-6` between major page sections and `gap-3`/`gap-4` within a section, everywhere, rather than picking spacing ad hoc per page."*

**12. Dark-mode readiness (not implemented, but structured for it)**
Using semantic Tailwind color tokens (`slate-*`, custom `brand`/`recall` scales) rather than raw hex values means a `dark:` variant pass later is additive, not a rewrite.
Edge case: hardcoded hex values scattered through components make retrofitting dark mode a full rewrite instead of an addition.
Repo: `frontend/tailwind.config.ts`.
*"I didn't build dark mode for the MVP, but I structured the token system so adding `dark:` variants later is additive rather than a rewrite — that's a deliberate scope cut, not an oversight."*

**13. Accessible color contrast as a design constraint**
Text/background pairs (`text-emerald-900` on `bg-emerald-50`, not `text-emerald-400` on white) were chosen to keep contrast ratios reasonable, not just "on-brand."
Edge case: light text on light backgrounds (a common Tailwind footgun with the 300–400 shades) fails WCAG contrast checks.
Repo: `frontend/components/review/RetrievalCard.tsx`.
*"I deliberately used darker shade numbers for text on light backgrounds rather than the lighter shades that look 'softer' but fail contrast checks."*

**14. PostCSS/Autoprefixer pipeline underneath Tailwind**
`postcss.config.js` wires Tailwind + Autoprefixer into the Next.js build — understanding this is what's actually generating the final CSS.
Edge case: Tailwind alone doesn't add vendor prefixes; Autoprefixer is what makes flexbox/grid utilities work across older browsers.
Repo: `frontend/postcss.config.js`.
*"I know Tailwind itself doesn't handle vendor prefixing — that's Autoprefixer running in the same PostCSS pipeline."*

**15. Single-file component styling (co-location)**
Every component's styling lives directly in its `.tsx` file via `className`, not in a separate `.module.css`.
Edge case: co-location means you never hunt across files to find what styles a component — but requires discipline (via `@layer components`) to avoid duplication.
Repo: every file in `frontend/components/**`.
*"I chose co-located utility classes over CSS Modules — trade-off is verbose JSX for the benefit of never context-switching between a component and its stylesheet."*

---

## 4. FastAPI / Pydantic — 15 concepts

**1. Automatic request validation from type hints**
`SubjectCreate(name: str = Field(..., min_length=1, max_length=120))` — FastAPI rejects malformed input with a 422 before your route body even runs.
Edge case: without `min_length=1`, an empty-string `name` would pass validation and create a garbage subject.
Repo: `backend/app/schemas/subject.py`.
*"I push validation into the schema layer so a route function only ever runs with already-valid data — no defensive `if not name` checks scattered through business logic."*

**2. Response models decouple internal shape from API contract**
`Question` (full internal model with `difficulty`, `review_count`) vs `QuestionCreate` (only what the client may send).
Edge case: without this split, a client could set `review_count` or `difficulty` directly in a POST body, corrupting the scheduler's invariants.
Repo: `backend/app/schemas/question.py`.
*"Server-owned fields like `next_review` and `difficulty` are structurally impossible for a client to set directly — that's enforced by the schema, not a runtime check."*

**3. Dependency injection via FastAPI's `Depends` (implicit here through config)**
`Settings` is a singleton read via `from app.config import settings`, functioning as poor-man's DI; a larger app would use `Depends(get_settings)`.
Edge case: global singletons make testing harder if you need different config per test — acknowledged trade-off for this app's size.
Repo: `backend/app/config.py`.
*"For this app's size I used a module-level settings singleton; at a larger scale I'd switch to FastAPI's `Depends()`-based injection so tests can override config per-request."*

**4. Async I/O throughout the request path**
Every route and every database method is `async def`, so FastAPI can serve other requests while one is awaiting I/O (a real Mongo call, in production).
Edge case: mixing sync blocking calls (e.g. a synchronous DB driver) into an async route silently blocks the entire event loop — a classic FastAPI production bug.
Repo: `backend/app/database.py`, every router.
*"Every I/O boundary in this app is `async` end-to-end, specifically so a slow DB call in production doesn't block the whole event loop — that's a real FastAPI footgun I designed around."*

**5. Path/query parameter typing with defaults**
`async def list_notes(topic_id: str | None = None)` — FastAPI parses `?topic_id=` into a properly-typed optional parameter automatically.
Edge case: without the `| None` default, the parameter becomes required and every existing call without it breaks with a 422.
Repo: `backend/app/routers/notes.py`.
*"I make filters like `topic_id` optional query params with explicit `None` defaults, so 'list everything' and 'list by topic' are the same endpoint."*

**6. HTTPException for explicit, typed error responses**
`raise HTTPException(status_code=404, detail="...")` instead of returning `None` or an ambiguous 200 with an error field.
Edge case: returning 200 with `{"error": "not found"}` forces every client to parse the body to detect failure instead of checking the status code.
Repo: `backend/app/routers/reviews.py`.
*"I raise HTTPException with real status codes rather than a 200-with-error-field pattern — the HTTP status code itself carries the semantics."*

**7. CORS as explicit middleware configuration**
`CORSMiddleware(allow_origins=settings.cors_origins)` — a named list, not a wildcard.
Edge case: `allow_origins=["*"]` combined with `allow_credentials=True` is actually rejected by browsers/spec — a real gotcha to know for an interview.
Repo: `backend/app/main.py`.
*"I know `allow_origins=['*']` with credentials enabled isn't just insecure, browsers actively reject that combination per spec — so origins are named explicitly."*

**8. Router modularity via `APIRouter` + prefixes**
Each domain (`subjects`, `questions`, `reviews`...) is its own `APIRouter` with its own `prefix` and `tags`, composed in `main.py`.
Edge case: putting every route in one file works until the file is 2,000 lines — this pattern scales by domain, not by growing one file.
Repo: `backend/app/routers/*.py`, composed in `backend/app/main.py`.
*"Routes are split by domain into separate `APIRouter`s, which is also what makes the auto-generated `/docs` grouped and readable at scale."*

**9. Business logic isolated from HTTP framework (testable without FastAPI)**
`scheduler.py`/`scoring.py`/`analytics.py` import nothing from `fastapi` — they're plain Python.
Edge case: logic tightly coupled to `Request`/`Response` objects can't be unit tested without spinning up the whole framework.
Repo: `backend/app/services/*.py`.
*"None of my business logic imports FastAPI at all — that's what let me write pure, framework-free unit tests that run in milliseconds."*

**10. Enum-based validation (`QuestionType`, `ReviewRating`)**
`class ReviewRating(str, Enum)` — Pydantic validates incoming strings against the enum automatically and rejects anything else with a 422.
Edge case: using a plain `str` field instead would silently accept a typo like `"gud"` and store garbage data.
Repo: `backend/app/schemas/review.py`.
*"I use `str, Enum` for any field with a closed set of valid values — it's both a runtime validator and a self-documenting API contract in the OpenAPI schema."*

**11. Settings management via `pydantic-settings` and env vars**
`class Settings(BaseSettings)` reads from environment variables / `.env`, with typed defaults (`use_in_memory_db: bool = True`).
Edge case: without typed settings, an env var like `"false"` (a string) can be truthy in naive Python code — `pydantic-settings` correctly coerces it to a real bool.
Repo: `backend/app/config.py`.
*"I know `bool("false")` is `True` in plain Python — that's exactly the class of bug typed settings via `pydantic-settings` eliminates."*

**12. Auto-generated OpenAPI docs as a contract, not an afterthought**
`/docs` and `/redoc` are generated automatically from the same Pydantic schemas that validate requests — no separate documentation to keep in sync.
Edge case: hand-written API docs drift from the actual implementation; generated docs structurally cannot.
Repo: entire `backend/app/schemas/*` + `backend/app/routers/*`.
*"The docs at `/docs` are generated from the same types that validate requests, so they can't drift out of sync the way hand-written API docs do."*

**13. `model_config = {"populate_by_name": True}` for `_id` aliasing**
MongoDB's `_id` field needs to map to a Python-friendly `id` while still accepting/returning `_id` over the wire — handled via Pydantic's `Field(alias="_id")`.
Edge case: without `populate_by_name`, you'd have to choose between clean Python attribute names and correct MongoDB field names — this lets you have both.
Repo: `backend/app/schemas/subject.py` and every schema with an `id` field.
*"MongoDB's `_id` convention and Python's naming convention conflict — Pydantic's `alias` + `populate_by_name` is the standard way to reconcile them without ugly `doc["_id"]` access everywhere."*

**14. Partial update schemas (`NoteUpdate`) with all-optional fields**
A PATCH endpoint's schema makes every field optional, then the route filters out `None` values before writing — true partial updates, not "resend everything."
Edge case: without filtering `None`s, a PATCH that only sends `{"title": "x"}` would accidentally null out every other field.
Repo: `backend/app/schemas/note.py`, `backend/app/routers/notes.py: update_note()`.
*"PATCH is implemented as a real partial update — I explicitly filter out unset fields before writing, otherwise a partial payload would null out the rest of the document."*

**15. Testing FastAPI apps via ASGI transport, not a live server**
`httpx.AsyncClient(transport=ASGITransport(app=app))` runs full HTTP-shaped requests directly against the app in-process — no port binding, no live server needed for tests.
Edge case: spinning up a real `uvicorn` process for integration tests is slow and flaky in CI; ASGI transport avoids that entirely.
Repo: `backend/tests/test_reviews.py`.
*"My integration tests exercise the real routing/validation/serialization stack through ASGI transport, without ever binding a port — that's why the whole suite runs in under a second."*

---

## 5. MongoDB / Database — 15 concepts

**1. Document model vs relational normalization trade-off**
Each `question` document embeds its own scheduling state (`next_review`, `difficulty`) rather than a separate `scheduling` table joined by foreign key.
Edge case: embedding is right when the data is always read/written together (as here); it's wrong when sub-documents grow unbounded (e.g. embedding every review inside a question would bloat the document).
Repo: `backend/app/schemas/question.py`, `docs/DATABASE.md`.
*"I embedded scheduling state directly in the question document since it's always read and written together — but kept `reviews` as its own collection since that list is unbounded and append-only."*

**2. Referencing via foreign-key-style IDs (`topic_id`, `subject_id`)**
Documents reference each other by string ID rather than deep nesting (a `note` references `topic_id`, not embedding the whole topic).
Edge case: MongoDB has no enforced foreign key constraint — a `topic_id` pointing at a deleted topic is a real possibility the app must handle (or prevent via app-level checks, as `create_topic` does by verifying the subject exists first).
Repo: `backend/app/routers/subjects.py: create_topic()` explicitly 404s if the parent subject doesn't exist.
*"MongoDB won't enforce referential integrity for me, so I added the existence check at the application layer instead of assuming the foreign key is always valid."*

**3. Indexing strategy for query patterns actually used**
`docs/DATABASE.md` documents a `(topic_id, next_review)` compound index specifically because `GET /questions/due` filters and would otherwise sort on both fields.
Edge case: not indexing this means `due_questions` does a full collection scan under real load — fine in the in-memory dev store, a real production issue at scale.
Repo: `docs/DATABASE.md`.
*"I designed the index around the actual query shape — `topic_id` equality plus a `next_review` range — rather than indexing every field defensively."*

**4. Abstraction layer for swappable persistence (Repository pattern)**
`get_collection(name)` returns either an in-memory store or a real Motor-backed collection behind one interface, so schema/business logic never imports `motor` directly.
Edge case: leaking Mongo-specific query syntax (like `$gte`) into a router would break the in-memory backend, which doesn't implement the full Mongo query language — this constrains the abstraction's design on purpose.
Repo: `backend/app/database.py`.
*"I deliberately kept the query interface to a small common subset — equality filters, not full Mongo query operators — specifically so the in-memory test double stays a faithful substitute."*

**5. Schema validation enforced at the application layer, not the database**
MongoDB is schemaless by default; Pydantic schemas are what actually guarantee document shape here.
Edge case: without app-level validation, a bug could insert a document missing a required field and MongoDB wouldn't complain — a real class of production bug specific to document databases.
Repo: every `backend/app/schemas/*.py` file, enforced before every `insert_one`.
*"Since MongoDB won't reject a malformed document, all shape/type guarantees come from Pydantic at the API boundary — I know that's a deliberate trade-off versus MongoDB's own JSON Schema validators, which I'd add for defense-in-depth in a real production deployment."*

**6. Aggregation logic kept out of raw Mongo aggregation pipelines for now**
`analytics.py`'s `topic_retention()`/`due_counts()` currently aggregate in Python after `find({})`, not via a MongoDB `$group` aggregation pipeline.
Edge case: this is fine at demo scale; at real scale, pulling every document into app memory to aggregate is the wrong move — the honest next step is a Mongo aggregation pipeline.
Repo: `backend/app/services/analytics.py`.
*"I know this aggregation should move into a MongoDB `$group`/`$bucket` pipeline once data volume grows — right now it's Python-side specifically to keep it testable against the in-memory store without needing real Mongo's aggregation engine."*

**7. Idempotency and write safety on the review-submission path**
Submitting a review is a two-step write (update the question's scheduling fields, then insert a review record) — not wrapped in a transaction here.
Edge case: without a transaction, a crash between the two writes leaves an inconsistent state (question rescheduled but no review record, or vice versa) — a real production concern flagged as a known limitation.
Repo: `backend/app/routers/reviews.py: submit_review()`.
*"This is a two-write operation without a transaction — I'd wrap it in a MongoDB multi-document transaction (replica-set required) before this went to real production, and I can point to exactly where that transaction boundary would go."*

**8. String IDs as the primary key convention, not raw `ObjectId`**
Every schema uses `id: str = Field(alias="_id")`, and the Motor adapter converts `ObjectId` to `str` on the way out.
Edge case: leaking a raw `ObjectId` into a JSON response fails to serialize (it's not JSON-native) — converting at the boundary avoids that entirely.
Repo: `backend/app/database.py: MotorCollectionAdapter.insert_one()`.
*"I convert `ObjectId` to `str` at the database-adapter boundary, once, so no route or schema anywhere else has to think about Mongo-specific types."*

**9. Read/write path separation between "hot" and "cold" data**
Frequently-read scheduling fields (`next_review`) live directly on the `question` document (hot path, read on every dashboard load); full review history lives in a separate `reviews` collection (cold path, read rarely).
Edge case: putting everything in one collection either bloats the hot document or makes the hot query join against a large collection unnecessarily.
Repo: `backend/app/schemas/question.py` vs `backend/app/schemas/review.py`.
*"I split frequently-read scheduling state from the append-only audit trail into two collections — that's the same hot/cold data separation instinct that scales to a real production data model."*

**10. Test isolation via a resettable in-memory store**
`reset_in_memory_db()` wipes all collections between tests via an autouse `pytest` fixture.
Edge case: without isolation, test order matters and tests interfere with each other's data — a classic source of flaky test suites.
Repo: `backend/app/database.py: reset_in_memory_db()`, `backend/tests/conftest.py`.
*"Every test starts from a clean, empty store — that's what makes `pytest -v` deterministic regardless of execution order."*

**11. Query filtering explicitly limited to equality (documented constraint)**
`InMemoryCollection.find()` only supports exact-match filters (`{"topic_id": x}`), not range queries — a conscious, documented limitation of the dev store.
Edge case: a developer writing `find({"next_review": {"$lt": now}})` against the in-memory store would silently get wrong results (since `$lt` isn't a real key to match), which is why `due_questions` deliberately filters in Python instead.
Repo: `backend/app/routers/questions.py: due_questions()` filters `is_due()` in Python rather than pushing a range query into `find()`.
*"I know exactly where my abstraction's query language stops — range queries — and I route around that limitation explicitly rather than accidentally relying on undefined behavior."*

**12. Timestamps and timezone-awareness**
Every `datetime` default uses `datetime.now(timezone.utc)`, never naive `datetime.now()`.
Edge case: naive datetimes silently compare incorrectly across timezones and are a notorious source of "off by N hours" bugs in production once a service has users in multiple timezones.
Repo: every schema file, e.g. `backend/app/schemas/subject.py`.
*"Every timestamp in this system is timezone-aware UTC — I've seen naive-datetime bugs before and designed them out from the schema level up."*

**13. Denormalized counters updated on write vs computed on read**
`question.review_count`/`correct_count` are denormalized counters incremented on every review, rather than computed by counting the `reviews` collection on every read.
Edge case: denormalization risks drift if the counter-update and the source-of-truth insert aren't kept in sync (see point 7's transaction discussion) — a real trade-off, not a free lunch.
Repo: `backend/app/routers/reviews.py: submit_review()`.
*"I denormalized review counters onto the question document for fast reads on the dashboard, and I can explain the exact consistency risk that trade-off introduces and how a transaction would close it."*

**14. Connection lifecycle for the real Mongo client**
The Motor client (`AsyncIOMotorClient`) is lazily constructed once and reused (`_motor_client`/`_motor_db` module-level singletons), not reconnected per-request.
Edge case: creating a new MongoClient per request exhausts connection pools under load — a real, well-known production mistake.
Repo: `backend/app/database.py: get_collection()`.
*"The Mongo client is a lazily-initialized singleton reused across requests — I know creating a new client per request is a classic way to exhaust a connection pool in production."*

**15. Migration/versioning strategy (acknowledged gap, not pretended away)**
This MVP has no schema migration tooling (no Alembic-equivalent for MongoDB) — a known, explicitly scoped-out gap.
Edge case: schemaless databases make it *easier* to ship a breaking field-rename, not harder — without discipline, old documents silently don't match new Pydantic schemas.
Repo: not implemented; flagged here deliberately.
*"MongoDB's flexibility cuts both ways — there's no schema migration tool enforcing consistency, so a field rename requires either a backfill script or defensive Optional handling in Pydantic for old documents. I didn't build migration tooling for the MVP, but I can talk through exactly how I'd add it — a versioned `schema_version` field per document plus a startup migration runner."*

---

## How to actually use this doc in an interview

Don't recite it. Pick **2–3 items per stack area** you can explain fluently
without looking, and be ready to open the actual file and point at the line
if asked "show me." The strongest fresher signal isn't breadth of
vocabulary — it's being able to say *"here's the naive version, here's why
I didn't ship that, here's the trade-off I actually made"* for a handful of
real decisions. That's what every item above is templated to give you.
