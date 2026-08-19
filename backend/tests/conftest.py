import pytest

from app.database import reset_in_memory_db


@pytest.fixture(autouse=True)
def _clean_db():
    """Reset the in-memory store before every test for isolation."""
    reset_in_memory_db()
    yield
    reset_in_memory_db()
