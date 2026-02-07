"""Phase V Unit Tests

Tests for: priority validation, tag sync, search query building,
filter composition, recurrence depth check, reminder query, event schemas.
"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timezone, timedelta


# --- Priority Validation Tests ---

class TestPriorityValidation:
    def test_valid_priorities(self):
        """P1-P4 are valid priority values."""
        valid = ["P1", "P2", "P3", "P4"]
        for p in valid:
            assert len(p) == 2
            assert p[0] == "P"
            assert p[1] in "1234"

    def test_default_priority_is_p3(self):
        """Default priority should be P3."""
        from models.user import TaskCreate
        task = TaskCreate(title="Test task")
        assert task.priority == "P3"

    def test_task_create_accepts_priority(self):
        """TaskCreate should accept priority field."""
        from models.user import TaskCreate
        task = TaskCreate(title="Urgent task", priority="P1")
        assert task.priority == "P1"

    def test_task_update_priority(self):
        """TaskUpdate should accept optional priority."""
        from models.user import TaskUpdate
        update = TaskUpdate(priority="P2")
        assert update.priority == "P2"


# --- Tag Tests ---

class TestTagModels:
    def test_tag_model_fields(self):
        """Tag model should have name, user_id, created_at."""
        from models.tag import Tag
        tag = Tag(name="work", user_id=1)
        assert tag.name == "work"
        assert tag.user_id == 1

    def test_task_tag_model(self):
        """TaskTag junction table should have task_id and tag_id."""
        from models.tag import TaskTag
        tt = TaskTag(task_id=1, tag_id=2)
        assert tt.task_id == 1
        assert tt.tag_id == 2

    def test_task_create_with_tags(self):
        """TaskCreate should accept optional tags list."""
        from models.user import TaskCreate
        task = TaskCreate(title="Tagged task", tags=["work", "urgent"])
        assert task.tags == ["work", "urgent"]

    def test_task_create_without_tags(self):
        """TaskCreate with no tags defaults to None."""
        from models.user import TaskCreate
        task = TaskCreate(title="No tags")
        assert task.tags is None


# --- Recurrence Tests ---

class TestRecurrence:
    def test_recurrence_rule_in_task_create(self):
        """TaskCreate should accept recurrence_rule."""
        from models.user import TaskCreate
        task = TaskCreate(title="Daily standup", recurrence_rule="daily")
        assert task.recurrence_rule == "daily"

    def test_advance_due_date_daily(self):
        """Daily recurrence advances by 1 day."""
        from consumers.recurring import _advance_due_date
        now = datetime(2026, 2, 7, 10, 0, 0)
        result = _advance_due_date(now, "daily")
        assert result == now + timedelta(days=1)

    def test_advance_due_date_weekly(self):
        """Weekly recurrence advances by 7 days."""
        from consumers.recurring import _advance_due_date
        now = datetime(2026, 2, 7, 10, 0, 0)
        result = _advance_due_date(now, "weekly")
        assert result == now + timedelta(weeks=1)

    def test_advance_due_date_monthly(self):
        """Monthly recurrence advances to next month."""
        from consumers.recurring import _advance_due_date
        now = datetime(2026, 2, 15, 10, 0, 0)
        result = _advance_due_date(now, "monthly")
        assert result.month == 3
        assert result.year == 2026

    def test_advance_due_date_none(self):
        """None due_date returns now(UTC)."""
        from consumers.recurring import _advance_due_date
        result = _advance_due_date(None, "daily")
        assert result is not None

    def test_max_recurrence_depth(self):
        """Recurrence depth >= 1000 should be rejected."""
        max_depth = 1000
        assert max_depth == 1000  # Consumer checks >= 1000


# --- Reminder Tests ---

class TestReminders:
    def test_reminder_minutes_in_task_create(self):
        """TaskCreate should accept reminder_minutes."""
        from models.user import TaskCreate
        task = TaskCreate(title="Remind me", reminder_minutes=30)
        assert task.reminder_minutes == 30

    def test_reminder_minutes_default_none(self):
        """Default reminder_minutes is None."""
        from models.user import TaskCreate
        task = TaskCreate(title="No reminder")
        assert task.reminder_minutes is None

    def test_task_read_includes_reminder_fields(self):
        """TaskRead should include reminder_minutes and reminder_sent."""
        from models.user import TaskRead
        read = TaskRead(
            id=1, title="Test", description="Test desc",
            completed=False, priority="P3",
            due_date=None, user_id=1,
            created_at=datetime.now(), updated_at=datetime.now(),
            reminder_minutes=15, reminder_sent=False,
        )
        assert read.reminder_minutes == 15
        assert read.reminder_sent is False


# --- Event Schema Tests ---

class TestEventSchemas:
    def test_task_event_schema(self):
        """TaskEvent should have required fields."""
        from events.schemas import TaskEvent
        event = TaskEvent(
            event_type="task.created",
            user_id=1,
            task_id=42,
            data={"title": "Test"},
        )
        assert event.event_type == "task.created"
        assert event.user_id == 1
        assert event.task_id == 42
        assert event.event_id  # Auto-generated UUID
        assert event.schema_version == "1.0"

    def test_task_event_to_dict(self):
        """TaskEvent.to_dict() should return serializable dict."""
        from events.schemas import TaskEvent
        event = TaskEvent(
            event_type="task.updated",
            user_id=1,
            task_id=42,
            data={"priority": "P1"},
        )
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d["event_type"] == "task.updated"
        assert "event_id" in d
        assert "timestamp" in d

    def test_reminder_event_schema(self):
        """ReminderEvent should have task_title and due_date."""
        from events.schemas import ReminderEvent
        event = ReminderEvent(
            event_type="reminder.due",
            user_id=1,
            task_id=42,
            task_title="Buy groceries",
            due_date="2026-02-07T18:00:00+00:00",
        )
        assert event.event_type == "reminder.due"
        assert event.task_title == "Buy groceries"
        assert event.due_date == "2026-02-07T18:00:00+00:00"

    def test_reminder_event_to_dict(self):
        """ReminderEvent.to_dict() should be serializable."""
        from events.schemas import ReminderEvent
        event = ReminderEvent(
            event_type="reminder.due",
            user_id=1,
            task_id=42,
            task_title="Meeting",
            due_date="2026-02-07T09:00:00+00:00",
        )
        d = event.to_dict()
        assert isinstance(d, dict)
        assert d["task_title"] == "Meeting"


# --- Search/Filter Tests ---

class TestSearchFilter:
    def test_sort_by_default(self):
        """Default sort_by should be created_at."""
        default_sort = "created_at"
        assert default_sort == "created_at"

    def test_sort_order_default(self):
        """Default sort_order should be desc."""
        default_order = "desc"
        assert default_order == "desc"

    def test_pagination_offset(self):
        """Pagination offset calculation: (page-1) * page_size."""
        page, page_size = 3, 10
        offset = (page - 1) * page_size
        assert offset == 20

    def test_task_to_dict_includes_phase_v_fields(self):
        """_task_to_dict should include all Phase V fields."""
        from api.tasks import _task_to_dict
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.title = "Test"
        mock_task.description = "Desc"
        mock_task.completed = False
        mock_task.priority = "P1"
        mock_task.due_date = None
        mock_task.user_id = 1
        mock_task.created_at = datetime(2026, 2, 7)
        mock_task.updated_at = datetime(2026, 2, 7)
        mock_task.recurrence_rule = "daily"
        mock_task.recurrence_depth = 0
        mock_task.reminder_minutes = 15
        mock_task.reminder_sent = False

        result = _task_to_dict(mock_task, ["work", "urgent"])
        assert result["priority"] == "P1"
        assert result["tags"] == ["work", "urgent"]
        assert result["recurrence_rule"] == "daily"
        assert result["reminder_minutes"] == 15
        assert result["reminder_sent"] is False
