# tests/test_memory.py
"""
Sanity tests for core memory operations.
"""
import pytest
from atlas_memory import add_memory, search_memory, init_db, engine


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Ensure database tables exist before tests."""
    init_db(engine)


class TestAddMemory:
    """Tests for add_memory function."""

    def test_add_memory_returns_id(self):
        """add_memory should return a positive integer ID."""
        memory_id = add_memory(
            user_id="test-user",
            content="This is a test memory",
            branch="test-branch"
        )
        assert isinstance(memory_id, int)
        assert memory_id > 0

    def test_add_memory_with_metadata(self):
        """add_memory should accept metadata."""
        memory_id = add_memory(
            user_id="test-user",
            content="Memory with metadata",
            metadata={"type": "test", "priority": 1},
            branch="test-branch"
        )
        assert memory_id > 0


class TestSearchMemory:
    """Tests for search_memory function."""

    def test_search_returns_list(self):
        """search_memory should return a list."""
        # Add a memory first
        add_memory(
            user_id="test-search-user",
            content="I love sunny beaches",
            branch="test-search-branch"
        )

        results = search_memory(
            user_id="test-search-user",
            query="beach vacation",
            top_k=5,
            branch="test-search-branch"
        )
        assert isinstance(results, list)

    def test_search_results_have_required_fields(self):
        """Each result should have id, text, metadata, score."""
        add_memory(
            user_id="test-fields-user",
            content="Testing result fields",
            branch="test-fields-branch"
        )

        results = search_memory(
            user_id="test-fields-user",
            query="testing",
            top_k=1,
            branch="test-fields-branch"
        )

        assert len(results) > 0
        result = results[0]
        assert "id" in result
        assert "text" in result
        assert "metadata" in result
        assert "score" in result

    def test_search_results_ordered_by_score(self):
        """Results should be ordered by score descending."""
        user_id = "test-order-user"
        branch = "test-order-branch"

        # Add multiple memories
        add_memory(user_id, "I love cats", branch=branch)
        add_memory(user_id, "Dogs are great pets", branch=branch)
        add_memory(user_id, "Cats are my favorite animals", branch=branch)

        results = search_memory(user_id, "cats", top_k=3, branch=branch)

        # Verify descending order
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_search_modes(self):
        """All three search modes should work."""
        user_id = "test-modes-user"
        branch = "test-modes-branch"

        add_memory(user_id, "Vector search test content", branch=branch)

        # Test each mode
        for mode in ["vector", "fulltext", "hybrid"]:
            results = search_memory(user_id, "search", top_k=1, branch=branch, mode=mode)
            assert isinstance(results, list)
