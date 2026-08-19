"""
Callbacks.

Concept being explored: LangChain's callback system lets you hook into
every step of a chain/agent's execution (LLM start/end, tool start/end,
chain start/end) without modifying the chain itself -- useful for logging,
latency tracking, and cost tracking in production.

This is the "observability" layer you'd point to if asked "how would you
debug or monitor an LLM pipeline in production?" -- the honest answer for
a real deployment is usually LangSmith (LangChain's hosted tracing tool),
but understanding the underlying callback interface is what lets you
implement a custom one (e.g. piping latency into your own metrics system).

Run: python -m app.agents.callbacks   (requires Ollama running locally)
"""
from __future__ import annotations

import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler


class LatencyLoggingCallback(BaseCallbackHandler):
    """A minimal custom callback: times each LLM call and prints it.

    In a real deployment this is where you'd emit a metric
    (e.g. `statsd.timing("llm.latency_ms", ...)`) instead of printing --
    the interface is the same either way.
    """

    def __init__(self) -> None:
        self._start_times: dict[UUID, float] = {}

    def on_llm_start(
        self, serialized: dict[str, Any], prompts: list[str], *, run_id: UUID, **kwargs
    ) -> None:
        self._start_times[run_id] = time.monotonic()

    def on_llm_end(self, response: Any, *, run_id: UUID, **kwargs) -> None:
        start = self._start_times.pop(run_id, None)
        if start is not None:
            elapsed_ms = (time.monotonic() - start) * 1000
            print(f"[callback] LLM call took {elapsed_ms:.0f}ms")


if __name__ == "__main__":
    from app.agents.llm import get_llm

    llm = get_llm()
    callback = LatencyLoggingCallback()
    response = llm.invoke(
        "Reply with exactly one word: 'ready'.",
        config={"callbacks": [callback]},
    )
    print("LLM said:", response.content)
