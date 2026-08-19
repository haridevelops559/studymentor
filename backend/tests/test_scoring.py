from app.services.scoring import check_feynman_coverage, score_session


def test_score_session_handles_zero_attempts():
    assert score_session(0, 0) == 0.0


def test_score_session_computes_percentage():
    assert score_session(10, 7) == 70.0


def test_feynman_coverage_flags_missing_ideas():
    explanation = (
        "Virtual memory lets a process use more address space than "
        "physical memory by mapping pages to disk."
    )
    checklist = [
        "What problem it solves",
        "How virtual to physical address translation works",
        "What happens on a page fault",
    ]
    result = check_feynman_coverage(explanation, checklist)

    # The explanation talks about address space/physical memory, so the
    # "virtual to physical" idea is picked up via keyword overlap...
    assert "How virtual to physical address translation works" in result.covered
    # ...but page faults are never mentioned, so that idea is flagged missing.
    assert "What happens on a page fault" in result.missing
    assert 0.0 <= result.coverage_ratio <= 1.0


def test_feynman_coverage_full_match():
    explanation = "acronym keyword story"
    checklist = ["acronym", "keyword", "story"]
    result = check_feynman_coverage(explanation, checklist)
    assert result.coverage_ratio == 1.0
    assert result.missing == []
