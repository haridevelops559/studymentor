"""
Retrievers.

Concept being explored: a Retriever's job is "given a query, return the
most relevant documents" -- it's the R in RAG (Retrieval-Augmented
Generation). Production RAG usually means embeddings + a vector database
(Chroma, Pinecone, MongoDB Atlas Vector Search...).

This file deliberately implements the *simplest possible* retriever --
keyword overlap over the student's own notes, no embeddings, no vector DB
-- for two honest reasons:
  1. It's minimally feasible to run and test with zero extra infrastructure.
  2. It's a legitimate first baseline: you should be able to explain *why*
     you'd upgrade to embeddings (semantic similarity, not just keyword
     overlap) before you actually add that infrastructure cost.

The upgrade path (documented, not built) would swap `KeywordNoteRetriever`
for a `Chroma`-backed retriever with the same `.get_relevant_documents()`
interface -- everything calling the retriever wouldn't need to change,
same adapter principle as `app/database.py`.

Run: python -m app.agents.retriever
"""
from __future__ import annotations

import re

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


def _tokenize(text: str) -> set[str]:
    return set(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())


class KeywordNoteRetriever(BaseRetriever):
    """Ranks notes by keyword overlap with the query. No embeddings."""

    notes: list[Document]

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        query_tokens = _tokenize(query)
        scored = []
        for doc in self.notes:
            overlap = len(query_tokens & _tokenize(doc.page_content))
            if overlap > 0:
                scored.append((overlap, doc))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [doc for _, doc in scored[:3]]


def build_demo_retriever() -> KeywordNoteRetriever:
    notes = [
        Document(
            page_content="Virtual memory lets a process use more address "
            "space than physical RAM by mapping pages to disk.",
            metadata={"topic": "Virtual Memory"},
        ),
        Document(
            page_content="React Hooks like useState and useEffect let "
            "function components hold state and side effects.",
            metadata={"topic": "React Hooks"},
        ),
        Document(
            page_content="A page fault occurs when a process accesses a "
            "page that isn't currently in physical memory.",
            metadata={"topic": "Virtual Memory"},
        ),
    ]
    return KeywordNoteRetriever(notes=notes)


if __name__ == "__main__":
    retriever = build_demo_retriever()
    results = retriever.invoke("what happens on a page fault")
    for doc in results:
        print(f"[{doc.metadata['topic']}] {doc.page_content}")
