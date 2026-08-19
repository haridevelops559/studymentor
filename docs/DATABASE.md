# Data model

Collections (MongoDB in production; same shape in the in-memory dev store):

## `subjects`
```
_id, name, description, created_at
```

## `topics`
```
_id, subject_id, name
```

## `notes`
```
_id, topic_id, title, content, cues[], summary, created_at, updated_at
```

## `questions`
```
_id, topic_id, question, answer, type, created_at,
last_reviewed, next_review, review_count, correct_count, difficulty
```
`difficulty` is an ease factor (SM-2-inspired), clamped between 1.3 and 3.5.
`next_review` is recalculated on every submitted review by
`app/services/scheduler.py`.

## `reviews`
```
_id, question_id, user_id, rating, given_answer, reviewed_at, next_review
```
One row per retrieval-practice attempt. This is what powers "reviews
today" and (eventually) per-question history.

## `study_sessions`
```
_id, user_id, started_at, ended_at, duration_seconds,
planned_activities[], questions_attempted, questions_correct, topics_reviewed[]
```

## `feynman_explanations`
```
_id, topic_id, user_id, explanation, checklist[], created_at, check_result
```
`check_result` is `{ covered[], missing[], coverage_ratio }`, computed by
`app/services/scoring.py:check_feynman_coverage`.

## Indexing notes (for a real MongoDB deployment)

- `questions`: index on `(topic_id, next_review)` to make `GET /questions/due`
  cheap.
- `reviews`: index on `(user_id, reviewed_at)` for "today's reviews" and
  future history views.
- `study_sessions`: index on `(user_id, started_at)`.

These aren't applied in the in-memory dev store (linear scan is fine at
demo scale) but should be added via Motor's `create_index` at startup before
this goes to production with real user volume.
