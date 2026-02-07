"""Agent context and result types.

Immutable per-request context for agent execution.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass(frozen=True)
class MessageHistory:
    """Single message in conversation history."""
    role: str  # "user" | "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[Dict[str, Any]]] = None


@dataclass(frozen=True)
class AgentContext:
    """Immutable context for a single agent invocation."""
    user_id: str
    conversation_id: str
    message_history: tuple  # Tuple of MessageHistory for immutability

    @classmethod
    def from_request(
        cls,
        user_id: str,
        conversation_id: str,
        messages: List[Dict[str, Any]]
    ) -> "AgentContext":
        """Create context from Chat API request data."""
        history = tuple(
            MessageHistory(
                role=m["role"],
                content=m["content"],
                timestamp=m.get("timestamp", datetime.utcnow()),
                tool_calls=m.get("tool_calls")
            )
            for m in messages
        )
        return cls(
            user_id=user_id,
            conversation_id=conversation_id,
            message_history=history
        )


@dataclass
class ToolCallRecord:
    """Record of a tool call made by the agent."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    duration_ms: int


@dataclass
class AgentResult:
    """Result of agent execution."""
    success: bool
    response: str
    tool_calls: List[ToolCallRecord] = field(default_factory=list)
    error: Optional[str] = None
    language: str = "en"

    @property
    def has_tool_calls(self) -> bool:
        """Check if agent made any tool calls."""
        return len(self.tool_calls) > 0
