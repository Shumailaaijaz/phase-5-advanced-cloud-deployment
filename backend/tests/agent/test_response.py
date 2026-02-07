"""Tests for response formatting."""

import pytest
from backend.agent.handlers.response import (
    format_task_created,
    format_task_list,
    format_task_completed,
    format_task_deleted,
    format_task_updated,
    format_error,
    format_ambiguous,
    format_greeting,
)


class TestTaskCreatedFormatting:
    """Tests for task creation confirmation."""

    def test_english_format(self):
        """English confirmation format."""
        result = format_task_created({"title": "Buy milk"}, "en")
        assert "Buy milk" in result
        assert "added" in result.lower()

    def test_urdu_format(self):
        """Urdu confirmation format."""
        result = format_task_created({"title": "Buy milk"}, "ur")
        assert "Buy milk" in result
        assert "شامل" in result

    def test_roman_urdu_format(self):
        """Roman Urdu confirmation format."""
        result = format_task_created({"title": "Buy milk"}, "roman_ur")
        assert "Buy milk" in result
        assert "add" in result.lower()


class TestTaskListFormatting:
    """Tests for task list formatting."""

    def test_formats_with_checkboxes(self):
        """Task list includes checkboxes."""
        data = {
            "tasks": [
                {"title": "Task 1", "completed": False},
                {"title": "Task 2", "completed": True},
            ]
        }
        result = format_task_list(data, "en")
        assert "☐" in result  # Uncompleted
        assert "✓" in result  # Completed

    def test_empty_list_message(self):
        """Empty list shows appropriate message."""
        result = format_task_list({"tasks": []}, "en")
        assert "don't have any tasks" in result.lower()

    def test_empty_list_urdu(self):
        """Empty list in Urdu."""
        result = format_task_list({"tasks": []}, "ur")
        assert "نہیں" in result  # "not" in Urdu


class TestTaskCompletedFormatting:
    """Tests for completion confirmation."""

    def test_english_completion(self):
        """English completion message."""
        result = format_task_completed({"title": "Buy milk"}, "en")
        assert "Buy milk" in result
        assert "complete" in result.lower()

    def test_all_languages(self):
        """Completion works in all languages."""
        for lang in ["en", "ur", "roman_ur"]:
            result = format_task_completed({"title": "Test"}, lang)
            assert "Test" in result


class TestErrorFormatting:
    """Tests for error message formatting."""

    def test_not_found_error(self):
        """Not found error is user-friendly."""
        result = format_error("not_found", lang="en")
        assert "couldn't find" in result.lower()
        # No technical details
        assert "404" not in result
        assert "error" not in result.lower()

    def test_not_found_urdu(self):
        """Not found in Urdu."""
        result = format_error("not_found", lang="ur")
        assert "نہیں ملا" in result  # "not found" in Urdu


class TestAmbiguousFormatting:
    """Tests for ambiguous match formatting."""

    def test_lists_options(self):
        """Ambiguous response lists options."""
        tasks = [{"title": "Buy milk"}, {"title": "Buy bread"}]
        result = format_ambiguous(tasks, "en")
        assert "Buy milk" in result
        assert "Buy bread" in result
        assert "multiple" in result.lower()


class TestGreetingFormatting:
    """Tests for greeting responses."""

    def test_greeting_is_friendly(self):
        """Greeting is friendly and helpful."""
        result = format_greeting("en")
        assert "help" in result.lower()

    def test_greeting_all_languages(self):
        """Greetings work in all languages."""
        for lang in ["en", "ur", "roman_ur"]:
            result = format_greeting(lang)
            assert len(result) > 0
