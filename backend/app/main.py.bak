from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import dashboard, feynman, notes, questions, reviews, sessions, subjects
app = FastAPI(
    title=settings.app_name,
    description=(
        "API for StudyMentor -- a study workflow built around retrieval "
        "practice, spaced repetition, and self-explanation."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(subjects.router, prefix=settings.api_prefix)
app.include_router(notes.router, prefix=settings.api_prefix)
app.include_router(questions.router, prefix=settings.api_prefix)
app.include_router(reviews.router, prefix=settings.api_prefix)
app.include_router(feynman.router, prefix=settings.api_prefix)
app.include_router(sessions.router, prefix=settings.api_prefix)
app.include_router(dashboard.router, prefix=settings.api_prefix)

# Optional, experimental: the Ollama/LangChain/LangGraph agent layer (see
# app/agents/ and docs/AGENT-LAYER-GUIDE.md). Guarded so a missing/broken
# optional dependency can never take down the core, tested API.
try:
    from app.routers import agents as agents_router

    app.include_router(agents_router.router, prefix=settings.api_prefix)
except Exception:  # noqa: BLE001
    pass


@app.get("/")
async def root():
    return {"service": settings.app_name, "status": "ok", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
