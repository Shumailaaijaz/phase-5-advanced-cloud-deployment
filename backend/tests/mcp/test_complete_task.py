"""Tests for complete_task MCP tool."""

import pytest
from backend.mcp.tools.complete_task import complete_task


class TestCompleteTask:
    """Test complete_task behavior."""

    def test_complete_existing_task(self, get_session, user_a, task_for_user_a):
        """Completing an existing task succeeds."""
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id)
        }

        result = complete_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["id"] == task_for_user_a.id
        assert result.data["completed"] is True

    def test_complete_already_completed_task_idempotent(
        self, get_session, user_a, completed_task_for_user_a
    ):
        """Completing already-completed task succeeds (idempotent)."""
        params = {
            "task_id": str(completed_task_for_user_a.id),
            "user_id": str(user_a.id)
        }

        result = complete_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["completed"] is True

    def test_complete_nonexistent_task_returns_not_found(self, get_session, user_a):
        """Completing non-existent task returns not_found."""
        params = {
            "task_id": "99999",
            "user_id": str(user_a.id)
        }

        result = complete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"
        assert result.error.details["task_id"] == "99999"

    def test_complete_other_user_task_returns_not_found(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """User A cannot complete User B's task (returns not_found)."""
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id)
        }

        result = complete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"
