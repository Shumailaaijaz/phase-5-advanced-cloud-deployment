"""Tests for language detection and templates."""

import pytest
from backend.agent.handlers.language import detect_language, is_urdu_script, is_roman_urdu
from backend.agent.templates.confirmations import get_template


class TestLanguageDetection:
    """Tests for detect_language function."""

    def test_detects_english(self):
        """English messages return 'en'."""
        assert detect_language("Add a task to buy milk") == "en"
        assert detect_language("Show my tasks") == "en"
        assert detect_language("Hello there!") == "en"

    def test_detects_urdu_script(self):
        """Urdu script messages return 'ur'."""
        assert detect_language("ٹاسک شامل کریں") == "ur"
        assert detect_language("میرے ٹاسکس دکھائیں") == "ur"
        assert detect_language("السلام علیکم") == "ur"

    def test_detects_roman_urdu(self):
        """Roman Urdu messages return 'roman_ur'."""
        assert detect_language("Task add karo") == "roman_ur"
        assert detect_language("Shukriya bhai") == "roman_ur"
        assert detect_language("Mera task complete kar do") == "roman_ur"

    def test_mixed_defaults_to_urdu_if_script_present(self):
        """Mixed messages with Urdu script default to 'ur'."""
        assert detect_language("Please مدد کریں") == "ur"

    def test_is_urdu_script(self):
        """Test is_urdu_script helper."""
        assert is_urdu_script("ٹاسک") is True
        assert is_urdu_script("task") is False

    def test_is_roman_urdu(self):
        """Test is_roman_urdu helper."""
        assert is_roman_urdu("Karo yeh kaam") is True
        assert is_roman_urdu("Do this work") is False


class TestTemplates:
    """Tests for confirmation templates."""

    def test_get_template_english(self):
        """Templates work in English."""
        result = get_template("task_created", "en", title="Buy milk")
        assert "Buy milk" in result
        assert "added" in result.lower()

    def test_get_template_urdu(self):
        """Templates work in Urdu."""
        result = get_template("task_created", "ur", title="Buy milk")
        assert "Buy milk" in result
        assert "شامل" in result  # Urdu word for "added"

    def test_get_template_roman_urdu(self):
        """Templates work in Roman Urdu."""
        result = get_template("task_created", "roman_ur", title="Buy milk")
        assert "Buy milk" in result
        assert "add" in result.lower()

    def test_all_template_types_exist(self):
        """All template types return non-empty strings."""
        template_types = [
            "task_created", "task_listed", "task_completed",
            "task_deleted", "task_updated", "task_not_found",
            "ambiguous_request", "greeting", "thanks"
        ]
        for t in template_types:
            for lang in ["en", "ur", "roman_ur"]:
                result = get_template(t, lang)
                assert result, f"Template {t} missing for {lang}"

    def test_unknown_template_returns_empty(self):
        """Unknown template type returns empty string."""
        assert get_template("nonexistent", "en") == ""
