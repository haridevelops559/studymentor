# Learning science behind StudyMentor

StudyMentor is **inspired by** research on effective learning techniques —
it is not a "scientifically proven learning system," and no single feature
should be marketed as guaranteeing better grades. Evidence quality varies
by technique, by material, and by learner, so the app frames every
technique as something to try, not a guarantee.

| Technique             | Product feature         | How it's framed in-app                          |
|------------------------|---------------------------|-----------------------------------------------------|
| Retrieval practice     | Retrieval-practice cards (`/review`, `/practice`) | Core loop — highest-utility technique      |
| Distributed practice   | Spaced-repetition scheduler (`services/scheduler.py`) | Core loop — reviews spread over time    |
| Self-explanation       | Feynman mode (`/feynman`) | Encouraged, framed as noticing your own gaps  |
| Interleaving           | Mixed-topic practice sessions (roadmap) | Presented as one option among several |
| Keyword mnemonics      | Memory Lab (roadmap)     | Framed as context-dependent, not universal    |
| Rereading               | Deliberately de-emphasized | Not a primary feature                        |

## Product-copy guidelines

- Never say a technique is "scientifically proven" to work for everyone.
- Prefer framing like *"try a mnemonic when it helps you encode and recall
  this material"* over absolute claims.
- Retrieval practice and distributed practice get the most product surface
  area because the evidence for them, across a range of materials and
  learners, is comparatively strong. Self-explanation and interleaving are
  offered as complementary techniques with more context-dependent evidence.

This file is meant to be the one place engineers and copywriters check
before adding language that oversells a feature's effect on learning
outcomes.
