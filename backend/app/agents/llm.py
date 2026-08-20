"""
LLM entrypoint for the agent layer.

This wraps a local Ollama model behind LangChain's `ChatOllama`, so every
other file in `app/agents/` depends on `get_llm()` rather than importing
`langchain_ollama` directly. That's the same adapter principle as
`app/database.py` for storage -- swap the model/provider in one place.

RUN THIS LOCALLY (not in this sandbox -- see docs/AGENT-LAYER-GUIDE.md):
    1. Install Ollama: https://ollama.com
    2. Pull a small, fast model:  ollama pull llama3.2:1b
    3. Start the server (usually automatic): ollama serve
    4. pip install -r backend/requirements-agents.txt
    5. python -m app.agents.llm        <-- self-test, see bottom of file
"""
from __future__ import annotations

import os

DEFAULT_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
DEFAULT_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")


def get_llm(temperature: float = 0.2, model: str | None = None):
    """
    Returns a LangChain ChatOllama instance.

    temperature=0.2 is deliberate: this app uses the LLM for structured,
    fact-grounded tasks (question generation from notes, coverage checks)
    where low variance matters more than creativity. Bump it for anything
    exploratory/creative.
    """
    from langchain_ollama import ChatOllama

    return ChatOllama(
        model=model or DEFAULT_MODEL,
        base_url=DEFAULT_BASE_URL,
        temperature=temperature,
    )


if __name__ == "__main__":
    # Minimal, standalone smoke test -- run this file directly to confirm
    # your local Ollama setup actually works before building anything on
    # top of it. This is step 1 of the "test file by file" workflow.
    llm = get_llm()
    response = llm.invoke("Reply with exactly one word: 'ready'.")
    print("LLM response:", response.content)
