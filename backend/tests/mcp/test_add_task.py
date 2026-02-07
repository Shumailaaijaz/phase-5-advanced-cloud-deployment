"""Tests for add_task MCP tool."""

import pytest
from backend.mcp.tools.add_task import add_task


class TestAddTaskSuccess:
    """Test add_task success cases."""

    def test_create_with_required_fields(self, get_session, user_a):
        """Create task with only required fields."""
        params = {
            "user_id": str(user_a.id),
            "title": "Buy groceries"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["title"] == "Buy groceries"
        assert result.data["priority"] == "Medium"
        assert result.data["completed"] is False
        assert result.data["description"] is None

    def test_create_with_all_fields(self, get_session, user_a):
        """Create task with all optional fields."""
        params = {
            "user_id": str(user_a.id),
            "title": "Complete project",
            "description": "Finish the MCP implementation",
            "priority": "High",
            "due_date": "2025-02-01"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["title"] == "Complete project"
        assert result.data["description"] == "Finish the MCP implementation"
        assert result.data["priority"] == "High"
        assert result.data["due_date"] == "2025-02-01"

    def test_task_has_correct_user_id(self, get_session, user_a):
        """Verify created task belongs to correct user."""
        params = {
            "user_id": str(user_a.id),
            "title": "User-specific task"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["user_id"] == str(user_a.id)


class TestAddTaskErrors:
    """Test add_task error cases."""

    def test_empty_title_returns_invalid_input(self, get_session, user_a):
        """Empty title should return invalid_input error."""
        params = {
            "user_id": str(user_a.id),
            "title": ""
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_input"

    def test_whitespace_title_returns_invalid_input(self, get_session, user_a):
        """Whitespace-only title should return invalid_input error."""
        params = {
            "user_id": str(user_a.id),
            "title": "   "
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_input"

    def test_invalid_priority_returns_error(self, get_session, user_a):
        """Invalid priority should return invalid_priority error."""
        params = {
            "user_id": str(user_a.id),
            "title": "Test task",
            "priority": "Urgent"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_priority"

    def test_invalid_date_returns_error(self, get_session, user_a):
        """Invalid date format should return invalid_date error."""
        params = {
            "user_id": str(user_a.id),
            "title": "Test task",
            "due_date": "01-02-2025"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "invalid_date"
