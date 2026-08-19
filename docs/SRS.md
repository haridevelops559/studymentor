# Software Requirements Specification — StudyMentor

## 1. Purpose

A personal study assistant that turns notes into retrieval practice, spaced
reviews, Feynman-style explanations, and lightweight study sessions, while
tracking retention over time.

## 2. Problem

Students commonly spend time rereading notes, highlighting, and re-watching
lectures — techniques with comparatively weak evidence for durable
learning — without a system for **learn → retrieve → explain → revisit →
measure retention**.

## 3. MVP scope

**In scope:**
- Subjects → Topics → Notes/Questions hierarchy
- Retrieval-practice question/answer flow with a 4-point recall rating
- A spaced-repetition scheduler that reschedules each question after every
  review
- Feynman-mode self-explanation with a lightweight coverage self-check
- Study sessions (start/finish, duration, questions attempted/correct)
- A dashboard aggregating due counts, retention by topic, and weak spots

**Explicitly out of scope for v1** (tracked as `v2` GitHub issues):
AI-generated questions, OAuth/authentication, payments, social/multiplayer
features, a native mobile app, a full calendar, an admin panel.

## 4. Functional requirements

- **FR-01 Notes** — create/edit subjects, topics, notes (title, content,
  cues, summary).
- **FR-02 Questions** — create questions, answer them, reveal the correct
  answer, rate recall difficulty.
- **FR-03 Review scheduling** — compute `next_review`, list due reviews,
  record review history.
- **FR-04 Feynman** — select a topic, write an explanation, get a
  keyword-overlap self-check against an optional checklist.
- **FR-05 Study sessions** — start/track/finish a session and persist its
  stats.
- **FR-06 Dashboard** — show today's due reviews, study time, recall %,
  and per-topic retention.

## 5. Non-functional requirements

- **Performance** — dashboard is a single aggregated endpoint so the
  frontend needs one request for the whole "today" view.
- **Reliability** — API validation errors return useful messages; failed
  writes surface as errors rather than silently dropping data.
- **Security (v1 baseline)** — no sensitive personal data collected; no
  authentication implemented yet (single implicit `demo-user`), so this
  should not be deployed with real user data until auth is added.

## 6. Architecture summary

Next.js (TypeScript, Tailwind) frontend → FastAPI backend → MongoDB
(Motor) in production, or an in-memory async store for local dev/tests.
See `docs/ARCHITECTURE.md` for details.
