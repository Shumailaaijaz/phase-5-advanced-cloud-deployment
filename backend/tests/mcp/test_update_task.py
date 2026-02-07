"""Tests for update_task MCP tool."""

import pytest
from backend.mcp.tools.update_task import update_task


class TestUpdateTaskSuccess:
    """Test update_task success cases."""

    def test_update_single_field(self, get_session, user_a, task_for_user_a):
        """Update single field succeeds."""
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id),
            "title": "Updated title"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["title"] == "Updated title"

    def test_update_multiple_fields(self, get_session, user_a, task_for_user_a):
        """Update multiple fields succeeds."""
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id),
            "title": "New title",
            "description": "New description",
            "priority": "High"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["title"] == "New title"
        assert result.data["description"] == "New description"
        assert result.data["priority"] == "High"

    def test_update_changes_updated_at(self, get_session, user_a, task_for_user_a):
        """Update modifies updated_at timestamp."""
        original_updated = task_for_user_a.updated_at
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id),
            "title": "Timestamp test"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["updated_at"] != original_updated.isoformat() + "Z"


class TestUpdateTaskErrors:
    """Test update_task error cases."""

    def test_no_fields_returns_invalid_input(self, get_session, user_a, task_for_user_a):
        """No update fields returns invalid_input."""
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id)
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_input"
        assert "at least one field" in result.error.message.lower()

    def test_invalid_priority_returns_error(self, get_session, user_a, task_for_user_a):
        """Invalid priority returns invalid_priority error."""
        params = {
            "task_id": str(task_for_user_a.id),
            "user_id": str(user_a.id),
            "priority": "Urgent"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_priority"

    def test_nonexistent_task_returns_not_found(self, get_session, user_a):
        """Update non-existent task returns not_found."""
        params = {
            "task_id": "99999",
            "user_id": str(user_a.id),
            "title": "Won't work"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"

    def test_other_user_task_returns_not_found(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """User A cannot update User B's task."""
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id),
            "title": "Hijacked title"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"
