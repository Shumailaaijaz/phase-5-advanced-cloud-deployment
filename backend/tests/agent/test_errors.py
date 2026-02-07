"""Tests for error handling."""

import pytest
from backend.agent.errors import to_friendly_message, map_tool_error


class TestFriendlyMessages:
    """Tests for error message conversion."""

    def test_not_found_english(self):
        """Not found error is friendly in English."""
        msg = to_friendly_message("not_found", "en")
        assert "couldn't find" in msg.lower()
        assert "error" not in msg.lower()
        assert "404" not in msg

    def test_not_found_urdu(self):
        """Not found error is friendly in Urdu."""
        msg = to_friendly_message("not_found", "ur")
        assert "نہیں ملا" in msg

    def test_not_found_roman_urdu(self):
        """Not found error is friendly in Roman Urdu."""
        msg = to_friendly_message("not_found", "roman_ur")
        assert "nahi mila" in msg.lower()

    def test_validation_error(self):
        """Validation error is friendly."""
        msg = to_friendly_message("validation_error", "en")
        assert "more details" in msg.lower() or "information" in msg.lower()

    def test_database_error(self):
        """Database error is friendly."""
        msg = to_friendly_message("database_error", "en")
        assert "try again" in msg.lower()
        # No technical details
        assert "database" not in msg.lower()
        assert "sql" not in msg.lower()

    def test_timeout_error(self):
        """Timeout error is friendly."""
        msg = to_friendly_message("timeout", "en")
        assert "longer than expected" in msg.lower()
        # No technical details
        assert "timeout" not in msg.lower() or "try again" in msg.lower()

    def test_unknown_error_fallback(self):
        """Unknown errors get generic friendly message."""
        msg = to_friendly_message("some_weird_error", "en")
        assert len(msg) > 0
        assert "went wrong" in msg.lower() or "try again" in msg.lower()


class TestToolErrorMapping:
    """Tests for mapping tool responses to friendly messages."""

    def test_maps_error_response(self):
        """Maps tool error response correctly."""
        response = {
            "success": False,
            "error": {"code": "not_found", "message": "Task not found"}
        }
        msg = map_tool_error(response, "en")
        assert "couldn't find" in msg.lower()

    def test_success_response_returns_empty(self):
        """Success response returns empty string."""
        response = {"success": True, "data": {}}
        msg = map_tool_error(response, "en")
        assert msg == ""

    def test_handles_missing_error(self):
        """Handles response without error field."""
        response = {"success": False}
        msg = map_tool_error(response, "en")
        assert msg == ""
