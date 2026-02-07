"""Tests for intent detection and task matching."""

import pytest
from backend.agent.handlers.intent import (
    match_task_by_title,
    detect_ambiguity,
    extract_task_reference,
    is_confirmation,
    is_greeting,
    is_thanks,
)


class TestTaskMatching:
    """Tests for task matching logic."""

    @pytest.fixture
    def sample_tasks(self):
        return [
            {"id": 1, "title": "Buy milk"},
            {"id": 2, "title": "Buy groceries"},
            {"id": 3, "title": "Call mom"},
        ]

    def test_exact_match(self, sample_tasks):
        """Exact title match returns single result."""
        matched, matches = match_task_by_title("Buy milk", sample_tasks)
        assert matched is not None
        assert matched["id"] == 1
        assert len(matches) == 1

    def test_substring_match(self, sample_tasks):
        """Substring match works."""
        matched, matches = match_task_by_title("milk", sample_tasks)
        assert matched is not None
        assert matched["id"] == 1

    def test_ambiguous_match(self, sample_tasks):
        """Multiple matches returns None with list."""
        matched, matches = match_task_by_title("Buy", sample_tasks)
        assert matched is None
        assert len(matches) == 2

    def test_no_match(self, sample_tasks):
        """No match returns empty list."""
        matched, matches = match_task_by_title("homework", sample_tasks)
        assert matched is None
        assert len(matches) == 0


class TestAmbiguityDetection:
    """Tests for ambiguity detection."""

    def test_single_match_not_ambiguous(self):
        """Single match is not ambiguous."""
        assert detect_ambiguity([{"id": 1}]) is False

    def test_multiple_matches_ambiguous(self):
        """Multiple matches are ambiguous."""
        assert detect_ambiguity([{"id": 1}, {"id": 2}]) is True

    def test_empty_not_ambiguous(self):
        """Empty list is not ambiguous."""
        assert detect_ambiguity([]) is False


class TestTaskReferenceExtraction:
    """Tests for extracting task references from messages."""

    def test_extracts_quoted_task(self):
        """Extracts task name from quotes."""
        ref = extract_task_reference("Complete the 'buy milk' task")
        assert ref is not None
        assert "milk" in ref.lower()

    def test_extracts_the_x_task_pattern(self):
        """Extracts 'the X task' pattern."""
        ref = extract_task_reference("Delete the grocery task")
        assert ref is not None


class TestConfirmation:
    """Tests for confirmation detection."""

    def test_english_yes(self):
        """English confirmations detected."""
        assert is_confirmation("yes") is True
        assert is_confirmation("yes delete") is True
        assert is_confirmation("confirm") is True

    def test_roman_urdu_yes(self):
        """Roman Urdu confirmations detected."""
        assert is_confirmation("haan") is True
        assert is_confirmation("ji") is True

    def test_not_confirmation(self):
        """Non-confirmations return False."""
        assert is_confirmation("maybe") is False
        assert is_confirmation("add task") is False


class TestGreeting:
    """Tests for greeting detection."""

    def test_english_greetings(self):
        """English greetings detected."""
        assert is_greeting("hi") is True
        assert is_greeting("hello") is True
        assert is_greeting("hey there") is True

    def test_urdu_greetings(self):
        """Urdu/Roman Urdu greetings detected."""
        assert is_greeting("Assalam o alaikum") is True
        assert is_greeting("السلام علیکم") is True

    def test_not_greeting(self):
        """Non-greetings return False."""
        assert is_greeting("add task") is False


class TestThanks:
    """Tests for thanks detection."""

    def test_english_thanks(self):
        """English thanks detected."""
        assert is_thanks("thanks") is True
        assert is_thanks("thank you") is True

    def test_urdu_thanks(self):
        """Urdu thanks detected."""
        assert is_thanks("shukriya") is True
        assert is_thanks("شکریہ") is True

    def test_not_thanks(self):
        """Non-thanks return False."""
        assert is_thanks("add task") is False
