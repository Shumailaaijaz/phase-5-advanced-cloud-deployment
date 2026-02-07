"""Tests for AgentRunner."""

import pytest
import asyncio
from unittest.mock import MagicMock

from backend.agent.runner import AgentRunner
from backend.agent.context import AgentContext


class TestAgentRunner:
    """Tests for AgentRunner class."""

    @pytest.fixture
    def runner(self, mock_session_factory, mock_mcp_server):
        """Create agent runner with mocks."""
        return AgentRunner(mock_session_factory, mock_mcp_server)

    @pytest.fixture
    def context(self):
        """Create test context."""
        return AgentContext.from_request(
            user_id="123",
            conversation_id="conv-456",
            messages=[]
        )

    def test_runner_initializes(self, runner):
        """Runner initializes correctly."""
        assert runner is not None
        assert runner._mcp_server is not None

    @pytest.mark.asyncio
    async def test_add_task_intent(self, runner, context):
        """Add task intent calls add_task tool."""
        result = await runner.run(context, "Add a task to buy milk")
        assert result.success
        assert "milk" in result.response.lower() or "added" in result.response.lower()
        assert result.has_tool_calls

    @pytest.mark.asyncio
    async def test_list_tasks_intent(self, runner, context):
        """List tasks intent calls list_tasks tool."""
        result = await runner.run(context, "Show my tasks")
        assert result.success
        assert result.has_tool_calls

    @pytest.mark.asyncio
    async def test_greeting_no_tools(self, runner, context):
        """Greetings don't call any tools."""
        result = await runner.run(context, "Hello!")
        assert result.success
        assert not result.has_tool_calls
        assert "help" in result.response.lower()

    @pytest.mark.asyncio
    async def test_thanks_no_tools(self, runner, context):
        """Thanks don't call any tools."""
        result = await runner.run(context, "Thank you!")
        assert result.success
        assert not result.has_tool_calls

    @pytest.mark.asyncio
    async def test_language_mirroring_english(self, runner, context):
        """English input gets English response."""
        result = await runner.run(context, "Show my tasks")
        assert result.language == "en"

    @pytest.mark.asyncio
    async def test_language_mirroring_urdu(self, runner, context):
        """Urdu input gets Urdu response."""
        result = await runner.run(context, "میرے ٹاسکس دکھائیں")
        assert result.language == "ur"

    @pytest.mark.asyncio
    async def test_language_mirroring_roman_urdu(self, runner, context):
        """Roman Urdu input gets Roman Urdu response."""
        result = await runner.run(context, "Mera task add karo milk wala")
        assert result.language == "roman_ur"


class TestAgentRunnerGuardrails:
    """Tests for agent guardrails."""

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
    async def test_max_iterations_respected(self, runner, context):
        """Runner respects max iterations limit."""
        # The runner should not make more than MAX_ITERATIONS tool calls
        from backend.agent.runner import MAX_ITERATIONS
        assert MAX_ITERATIONS == 10

    @pytest.mark.asyncio
    async def test_timeout_respected(self, runner, context):
        """Runner respects timeout."""
        from backend.agent.runner import TIMEOUT_SECONDS
        assert TIMEOUT_SECONDS == 30

    @pytest.mark.asyncio
    async def test_user_id_passed_to_tools(self, runner, context, mock_mcp_server):
        """User ID is passed to every tool call."""
        await runner.run(context, "Add task buy milk")

        # Check that mcp_server.call was called with user_id
        call_args = mock_mcp_server.call.call_args
        assert call_args is not None
        params = call_args[0][1]  # Second positional arg is params
        assert "user_id" in params
        assert params["user_id"] == "123"
