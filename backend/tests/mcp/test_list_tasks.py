"""Tests for list_tasks MCP tool."""

import pytest
from datetime import datetime, timedelta

from sqlmodel import Session
from backend.models.user import Task
from backend.mcp.tools.list_tasks import list_tasks


class TestListTasks:
    """Test list_tasks behavior."""

    def test_returns_user_tasks(self, get_session, session, user_a, task_for_user_a):
        """Returns tasks belonging to the user."""
        params = {"user_id": str(user_a.id)}

        result = list_tasks(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["total"] == 1
        assert len(result.data["tasks"]) == 1
        assert result.data["tasks"][0]["title"] == "User A's task"

    def test_returns_empty_array_for_no_tasks(self, get_session, user_a):
        """Returns empty array when user has no tasks."""
        params = {"user_id": str(user_a.id)}

        result = list_tasks(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["total"] == 0
        assert result.data["tasks"] == []

    def test_does_not_return_other_user_tasks(
        self, get_session, session, user_a, user_b, task_for_user_a, task_for_user_b
    ):
        """User A cannot see User B's tasks (isolation)."""
        params = {"user_id": str(user_a.id)}

        result = list_tasks(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["total"] == 1
        for task in result.data["tasks"]:
            assert task["user_id"] == str(user_a.id)

    def test_tasks_ordered_by_created_at_desc(self, get_session, session, user_a):
        """Tasks should be ordered newest first."""
        older_task = Task(
            user_id=user_a.id,
            title="Older task",
            priority="Low",
            completed=False,
            created_at=datetime.utcnow() - timedelta(days=1),
            updated_at=datetime.utcnow() - timedelta(days=1),
        )
        newer_task = Task(
            user_id=user_a.id,
            title="Newer task",
            priority="High",
            completed=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(older_task)
        session.add(newer_task)
        session.commit()

        params = {"user_id": str(user_a.id)}
        result = list_tasks(params, get_session, user_a.id)

        assert result.success is True
        assert result.data["total"] == 2
        assert result.data["tasks"][0]["title"] == "Newer task"
        assert result.data["tasks"][1]["title"] == "Older task"
