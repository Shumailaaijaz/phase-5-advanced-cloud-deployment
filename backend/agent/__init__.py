"""AI Agent Loop Module

The reasoning layer that interprets user messages, invokes MCP tools,
and generates natural language responses.
"""

from agent.context import AgentContext, AgentResult, MessageHistory
from agent.runner import AgentRunner
from agent.handlers.language import detect_language
from agent.templates.confirmations import get_template

__all__ = [
    "AgentRunner",
    "AgentContext",
    "AgentResult",
    "MessageHistory",
    "detect_language",
    "get_template",
]
