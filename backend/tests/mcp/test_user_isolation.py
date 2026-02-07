"""Cross-user isolation test suite.

Verifies that all MCP tools properly isolate user data.
"""

import pytest
from backend.mcp.tools import (
    add_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
)


class TestUserIsolation:
    """Verify user isolation across all tools."""

    def test_add_task_creates_for_authenticated_user(
        self, get_session, user_a, user_b
    ):
        """Task is created for authenticated user."""
        params = {
            "user_id": str(user_a.id),
            "title": "Test isolation"
        }

        result = add_task(params, get_session, user_a.id)

        assert result.success is True
        list_result = list_tasks(
            {"user_id": str(user_a.id)},
            get_session,
            user_a.id
        )
        assert list_result.data["total"] == 1

    def test_list_tasks_only_returns_own_tasks(
        self, get_session, session, user_a, user_b, task_for_user_a, task_for_user_b
    ):
        """Each user only sees their own tasks."""
        result_a = list_tasks({"user_id": str(user_a.id)}, get_session, user_a.id)
        assert result_a.data["total"] == 1
        assert all(t["user_id"] == str(user_a.id) for t in result_a.data["tasks"])

        result_b = list_tasks({"user_id": str(user_b.id)}, get_session, user_b.id)
        assert result_b.data["total"] == 1
        assert all(t["user_id"] == str(user_b.id) for t in result_b.data["tasks"])

    def test_complete_task_blocked_for_other_user(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """Cannot complete another user's task."""
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id)
        }

        result = complete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"

    def test_delete_task_blocked_for_other_user(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """Cannot delete another user's task."""
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id)
        }

        result = delete_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"

        list_result = list_tasks(
            {"user_id": str(user_b.id)},
            get_session,
            user_b.id
        )
        assert list_result.data["total"] == 1

    def test_update_task_blocked_for_other_user(
        self, get_session, user_a, user_b, task_for_user_b
    ):
        """Cannot update another user's task."""
        original_title = task_for_user_b.title
        params = {
            "task_id": str(task_for_user_b.id),
            "user_id": str(user_a.id),
            "title": "Hijacked!"
        }

        result = update_task(params, get_session, user_a.id)

        assert result.success is False
        assert result.error.code == "not_found"

        list_result = list_tasks(
            {"user_id": str(user_b.id)},
            get_session,
            user_b.id
        )
        assert list_result.data["tasks"][0]["title"] == original_title

    def test_no_data_leakage_across_users(
        self, get_session, session, user_a, user_b
    ):
        """Create tasks for both users and verify complete isolation."""
        for i in range(3):
            add_task(
                {"user_id": str(user_a.id), "title": f"A-Task-{i}"},
                get_session,
                user_a.id
            )

        for i in range(2):
            add_task(
                {"user_id": str(user_b.id), "title": f"B-Task-{i}"},
                get_session,
                user_b.id
            )

        result_a = list_tasks({"user_id": str(user_a.id)}, get_session, user_a.id)
        result_b = list_tasks({"user_id": str(user_b.id)}, get_session, user_b.id)

        assert result_a.data["total"] == 3
        assert result_b.data["total"] == 2

        for task in result_a.data["tasks"]:
            assert task["title"].startswith("A-Task")
        for task in result_b.data["tasks"]:
            assert task["title"].startswith("B-Task")
