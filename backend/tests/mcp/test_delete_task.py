"""Tests for delete_task MCP tool."""

import pytest
from backend.mcp.tools.delete_task import delete_task


class TestDeleteTask:
    """Test delete_task behavior."""

    def test_delete_existing_task(self, get_session, user_a, task_for_user_a):
        """Deleting an existing task succeeds."""
        task_id = str(task_for_user_a.id)
        params = {
            "task_id": task_id,
            "user_id": str(user_a.id)
        }

        result = delete_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["deleted"] is True
        assert result.data["task_id"] == task_id

    def test_delete_nonexistent_task_returns_not_found(self, get_session, user_a):
        """Deleting non-existent task returns not_found."""
        params = {
            "task_id": "99999",
            "user_id": str(user_a.id)
        }

        result = delete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"
        assert result.error.details["task_id"] == "99999"

    def test_delete_other_user_task_returns_not_found(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """User A cannot delete User B's task (returns not_found)."""
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id)
        }

        result = delete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"
