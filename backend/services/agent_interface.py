"""Agent interface for chat processing.

Wires the OpenAI-powered AgentRunner with MCP tools for task management.
Imports are deferred to avoid double-loading SQLModel tables.
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ChatAgentRunner:
    """Wraps the OpenAI AgentRunner for use by the chat endpoint."""

    def __init__(self):
        # Lazy import to avoid circular / double-registration issues
        from mcp.server import MCPToolServer
        from agent.openai_runner import OpenAIAgentRunner
        from database.session import engine

        # get_session is a generator (FastAPI dep), MCP tools need a plain factory
        def session_factory():
            from sqlmodel import Session
            return Session(engine)

        self._mcp_server = MCPToolServer(session_factory=session_factory)
        self._runner = OpenAIAgentRunner(
            session_factory=session_factory,
            mcp_server=self._mcp_server,
        )

    def process(self, messages: List[Dict[str, Any]], user_id: str = "", conversation_id: str = "") -> Dict[str, Any]:
        """Sync wrapper - runs the async agent and returns response with tool calls.

        Returns dict with 'response' and 'tool_calls' keys.
        """
        import asyncio
        from agent.context import AgentContext, AgentResult

        context = AgentContext.from_request(
            user_id=user_id,
            conversation_id=conversation_id,
            messages=messages,
        )

        last_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                last_message = msg.get("content", "")
                break

        if not last_message:
            return {
                "response": "I didn't understand your request. Could you please try again?",
                "tool_calls": []
            }

        try:
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                result: AgentResult = pool.submit(
                    asyncio.run, self._runner.run(context, last_message)
                ).result(timeout=60)  # 60 second timeout

            # Convert tool calls to response format
            tool_calls = [
                {
                    "tool_name": tc.tool_name,
                    "status": "completed" if result.success else "error",
                    "summary": f"{tc.tool_name.replace('_', ' ').title()}"
                }
                for tc in result.tool_calls
            ]

            return {
                "response": result.response,
                "tool_calls": tool_calls
            }

        except concurrent.futures.TimeoutError:
            logger.error("Agent execution timed out after 60 seconds")
            return {
                "response": "Request timed out. Please try again.",
                "tool_calls": []
            }
        except Exception as e:
            logger.exception(f"Agent interface error: {e}")
            return {
                "response": f"Error: {str(e)}",
                "tool_calls": []
            }


_agent_instance: Optional[ChatAgentRunner] = None


def get_agent_runner() -> ChatAgentRunner:
    """Get the agent runner instance (singleton)."""
    global _agent_instance
    if _agent_instance is None:
        _agent_instance = ChatAgentRunner()
    return _agent_instance
