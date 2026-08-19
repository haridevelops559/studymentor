# Agent experiments scratch space

This folder is intentionally empty of code. Use it as your own scratch
space while working through `docs/AGENT-LAYER-GUIDE.md` -- copy a file
from `app/agents/` in here, break it, fix it, and understand it before
touching the "real" copy. Nothing in here is imported by the app, so you
can experiment freely without breaking `pytest`.

Suggested first exercise: copy `app/agents/tools.py` in here and add a
third `@tool` that wraps `app/services/analytics.py: weakest_topics()`.
