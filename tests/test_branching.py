# tests/test_branching.py
"""
Sanity tests for branching (time travel) operations.
"""
import pytest
from atlas_memory import (
    add_memory,
    search_memory,
    save_point,
    load_point,
    delete_branch,
    list_branches,
    init_db,
    engine
)


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    """Ensure database tables exist before tests."""
    init_db(engine)


class TestBranchIsolation:
    """Tests for branch isolation - the core branching feature."""

    def test_branches_are_isolated(self):
        """Memories in one branch should not appear in another."""
        user_id = "test-isolation-user"

        # Add memory to main
        add_memory(user_id, "Main branch memory", branch="main")

        # Add memory to a different branch
        add_memory(user_id, "Other branch memory", branch="other-branch")

        # Search main - should not find "other-branch" content
        main_results = search_memory(user_id, "other branch", branch="main")
        main_texts = [r["text"] for r in main_results]
        assert "Other branch memory" not in main_texts

        # Search other-branch - should not find "main" content
        other_results = search_memory(user_id, "main branch", branch="other-branch")
        other_texts = [r["text"] for r in other_results]
        assert "Main branch memory" not in other_texts


class TestSavePoint:
    """Tests for save_point function."""

    def test_save_point_creates_branch(self):
        """save_point should create a new branch with copied memories."""
        user_id = "test-savepoint-user"

        # Add memories to main
        add_memory(user_id, "Original memory 1", branch="main")
        add_memory(user_id, "Original memory 2", branch="main")

        # Create savepoint
        new_branch = save_point(user_id, "snapshot", source_branch="main")

        # New branch should have the memories
        results = search_memory(user_id, "original memory", branch=new_branch)
        assert len(results) >= 2

    def test_save_point_returns_unique_name(self):
        """save_point should return a unique branch name with timestamp."""
        user_id = "test-unique-user"
        add_memory(user_id, "Some memory", branch="main")

        branch1 = save_point(user_id, "test", source_branch="main")
        branch2 = save_point(user_id, "test", source_branch="main")

        assert branch1 != branch2
        assert branch1.startswith("test-")
        assert branch2.startswith("test-")


class TestLoadPoint:
    """Tests for load_point function."""

    def test_load_point_returns_branch_name(self):
        """load_point should return the branch name."""
        result = load_point("my-branch")
        assert result == "my-branch"


class TestDeleteBranch:
    """Tests for delete_branch function."""

    def test_delete_branch_removes_memories(self):
        """delete_branch should remove all memories for that branch."""
        user_id = "test-delete-user"
        branch = "delete-me-branch"

        # Add memories
        add_memory(user_id, "Memory to delete 1", branch=branch)
        add_memory(user_id, "Memory to delete 2", branch=branch)

        # Delete branch
        deleted = delete_branch(user_id, branch)
        assert deleted >= 2

        # Verify memories are gone
        results = search_memory(user_id, "memory to delete", branch=branch)
        assert len(results) == 0

    def test_cannot_delete_main_branch(self):
        """delete_branch should raise error for main branch."""
        with pytest.raises(ValueError, match="Cannot delete the main branch"):
            delete_branch("any-user", "main")


class TestListBranches:
    """Tests for list_branches function."""

    def test_list_branches_returns_list(self):
        """list_branches should return a list of branch names."""
        user_id = "test-list-user"

        # Add memories to different branches
        add_memory(user_id, "Main memory", branch="main")
        add_memory(user_id, "Branch A memory", branch="branch-a")

        branches = list_branches(user_id)

        assert isinstance(branches, list)
        assert "main" in branches
        assert "branch-a" in branches
