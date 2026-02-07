"""Integration tests for agent module."""

import pytest
from unittest.mock import MagicMock
from backend.agent.runner import AgentRunner
from backend.agent.context import AgentContext


class TestUserIsolation:
    """Tests for user isolation guarantees."""

    @pytest.fixture
    def runner(self, mock_session_factory, mock_mcp_server):
        return AgentRunner(mock_session_factory, mock_mcp_server)

    def make_context(self, user_id: str):
        return AgentContext.from_request(
            user_id=user_id,
            conversation_id="conv-123",
            messages=[]
        )

    @pytest.mark.asyncio
    async def test_user_id_in_add_task(self, runner, mock_mcp_server):
        """User ID passed to add_task."""
        context = self.make_context("123")
        await runner.run(context, "Add task buy milk")

        call = mock_mcp_server.call.call_args
        assert call[0][1]["user_id"] == "123"

    @pytest.mark.asyncio
    async def test_user_id_in_list_tasks(self, runner, mock_mcp_server):
        """User ID passed to list_tasks."""
        context = self.make_context("456")
        await runner.run(context, "Show my tasks")

        call = mock_mcp_server.call.call_args
        assert call[0][1]["user_id"] == "456"

    @pytest.mark.asyncio
    async def test_different_users_isolated(self, runner, mock_mcp_server):
        """Different users get their own user_id in calls."""
        context_a = self.make_context("111")
        context_b = self.make_context("222")

        await runner.run(context_a, "Show my tasks")
        call_a = mock_mcp_server.call.call_args[0][1]["user_id"]

        await runner.run(context_b, "Show my tasks")
        call_b = mock_mcp_server.call.call_args[0][1]["user_id"]

        assert call_a == "111"
        assert call_b == "222"


class TestStatelessness:
    """Tests for stateless behavior."""

    @pytest.fixture
    def runner(self, mock_session_factory, mock_mcp_server):
        return AgentRunner(mock_session_factory, mock_mcp_server)

    @pytest.fixture
    def context(self):
        return AgentContext.from_request(
            user_id="123",
            conversation_id="conv-456",
            messages=[]
        )

    @pytest.mark.asyncio
    async def test_no_state_between_runs(self, runner, context, mock_mcp_server):
        """State doesn't persist between run() calls."""
        # First call
        result1 = await runner.run(context, "Show my tasks")

        # Second call should be independent
        result2 = await runner.run(context, "Show my tasks")

        # Both should succeed independently
        assert result1.success
        assert result2.success

    def test_context_is_immutable(self, context):
        """AgentContext is immutable (frozen dataclass)."""
        with pytest.raises(Exception):  # FrozenInstanceError
            context.user_id = "different"


class TestLanguageMirroring:
    """Tests for language mirroring integration."""

    @pytest.fixture
    def runner(self, mock_session_factory, mock_mcp_server):
        return AgentRunner(mock_session_factory, mock_mcp_server)

    @pytest.fixture
    def context(self):
        return AgentContext.from_request(
            user_id="123",
            conversation_id="conv-456",
            messages=[]
        )

    @pytest.mark.asyncio
    async def test_english_input_english_output(self, runner, context):
        """English input produces English response."""
        result = await runner.run(context, "Hello!")
        assert result.language == "en"
        # Response should be in English
        assert any(word in result.response.lower() for word in ["help", "hi", "hello"])

    @pytest.mark.asyncio
    async def test_urdu_input_urdu_output(self, runner, context):
        """Urdu input produces Urdu response."""
        result = await runner.run(context, "السلام علیکم")
        assert result.language == "ur"

    @pytest.mark.asyncio
    async def test_roman_urdu_input_roman_urdu_output(self, runner, context):
        """Roman Urdu input produces Roman Urdu response."""
        result = await runner.run(context, "Assalam o alaikum bhai")
        assert result.language == "roman_ur"


class TestToolCallRecording:
    """Tests for tool call recording."""

    @pytest.fixture
    def runner(self, mock_session_factory, mock_mcp_server):
        return AgentRunner(mock_session_factory, mock_mcp_server)

    @pytest.fixture
    def context(self):
        return AgentContext.from_request(
            user_id="123",
            conversation_id="conv-456",
            messages=[]
        )

    @pytest.mark.asyncio
    async def test_tool_calls_recorded(self, runner, context):
        """Tool calls are recorded in result."""
        result = await runner.run(context, "Add task buy milk")
        assert result.has_tool_calls
        assert len(result.tool_calls) >= 1
        assert result.tool_calls[0].tool_name == "add_task"

    @pytest.mark.asyncio
    async def test_tool_call_duration_recorded(self, runner, context):
        """Tool call duration is recorded."""
        result = await runner.run(context, "Add task buy milk")
        assert result.tool_calls[0].duration_ms >= 0

    @pytest.mark.asyncio
    async def test_no_tools_for_greeting(self, runner, context):
        """Greetings don't record tool calls."""
        result = await runner.run(context, "Hi!")
        assert not result.has_tool_calls
        assert len(result.tool_calls) == 0
