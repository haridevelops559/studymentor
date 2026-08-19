"""
Scoring helpers for retrieval practice and Feynman-style self-explanation.

Kept deliberately simple and dependency-free (no AI call required) so the
MVP works offline and is trivially unit-testable. These can later be swapped
for an LLM-backed implementation behind the same function signatures.
"""
from __future__ import annotations

import re

from app.schemas.feynman import FeynmanCheckResult


def _normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9\s]", "", text.lower()).strip()


def _tokenize(text: str) -> set[str]:
    return set(_normalize(text).split())


_STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "of", "to", "and", "or",
    "in", "on", "for", "it", "this", "that", "with", "as", "by", "be",
}


def check_feynman_coverage(
    explanation: str, checklist: list[str]
) -> FeynmanCheckResult:
    """
    Naive keyword-overlap check: for each checklist item, see whether its
    meaningful (non-stopword) terms appear in the student's explanation.

    This intentionally does NOT grade correctness -- self-explanation is
    about the student noticing gaps in their own account, so we surface
    "did you mention X?" rather than pretending to verify understanding.
    """
    explanation_tokens = _tokenize(explanation)

    covered: list[str] = []
    missing: list[str] = []

    for item in checklist:
        item_tokens = _tokenize(item) - _STOPWORDS
        if not item_tokens:
            continue
        overlap = item_tokens & explanation_tokens
        # Require meaningful overlap (at least half the key terms present).
        if len(overlap) >= max(1, len(item_tokens) // 2):
            covered.append(item)
        else:
            missing.append(item)

    total = len(covered) + len(missing)
    coverage_ratio = round(len(covered) / total, 2) if total else 0.0

    return FeynmanCheckResult(
        covered=covered, missing=missing, coverage_ratio=coverage_ratio
    )


def score_session(questions_attempted: int, questions_correct: int) -> float:
    """Recall percentage for a study session, guarding against division by 0."""
    if questions_attempted == 0:
        return 0.0
    return round(100 * questions_correct / questions_attempted, 1)
