"""
Memory.

Concept being explored: "memory" in LangChain means giving a chain/agent
access to prior turns of a conversation, so it can answer "what did I just
say?" instead of treating every call as stateless.

Modern LangChain (0.3+) deprecated the old `ConversationBufferMemory`
class in favor of managing message history explicitly via
`InMemoryChatMessageHistory` + `RunnableWithMessageHistory` -- which is
also a better teaching example, because it makes the state explicit rather
than hiding it inside a memory object.

In this app, memory would back a "study-coach chat" feature (roadmap item,
not built into the MVP UI) where a student can ask "why did you schedule
that review for tomorrow?" and get an answer grounded in the actual
conversation.

Run: python -m app.agents.memory
"""
from __future__ import annotations

from langchain_core.chat_history import InMemoryChatMessageHistory

# Keyed by session_id (e.g. a user_id or a browser session token) so
# multiple students/sessions don't share history. A production version
# would back this with Redis or the same Mongo collection pattern as
# app/database.py, not a plain dict.
_SESSION_STORE: dict[str, InMemoryChatMessageHistory] = {}


def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in _SESSION_STORE:
        _SESSION_STORE[session_id] = InMemoryChatMessageHistory()
    return _SESSION_STORE[session_id]


if __name__ == "__main__":
    history = get_session_history("demo-user")
    history.add_user_message("Why is Operating Systems flagged as weak?")
    history.add_ai_message(
        "Because your retention on it is 54%, the lowest of your tracked topics."
    )
    history.add_user_message("What should I review first?")

    print("Conversation so far:")
    for message in history.messages:
        print(f"  [{message.type}] {message.content}")
