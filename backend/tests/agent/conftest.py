"""Test fixtures for agent tests."""

import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime

from backend.agent.context import AgentContext, MessageHistory


@pytest.fixture
def mock_mcp_server():
    """Create mock MCP server with predictable responses."""
    server = MagicMock()

    # Default responses
    server.call = MagicMock(side_effect=lambda tool, params, user_id: {
        "add_task": {
            "success": True,
            "data": {
                "id": 1,
                "user_id": str(user_id),
                "title": params.get("title", "Test Task"),
                "completed": False,
                "priority": params.get("priority", "Medium"),
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
            }
        },
        "list_tasks": {
            "success": True,
            "data": {
                "tasks": [
                    {"id": 1, "title": "Buy milk", "completed": False, "priority": "Medium"},
                    {"id": 2, "title": "Call mom", "completed": False, "priority": "High"},
                    {"id": 3, "title": "Buy groceries", "completed": True, "priority": "Low"},
                ],
                "total": 3
            }
        },
        "complete_task": {
            "success": True,
            "data": {
                "id": int(params.get("task_id", 1)),
                "title": "Buy milk",
                "completed": True,
            }
        },
        "delete_task": {
            "success": True,
            "data": {"deleted": True, "task_id": params.get("task_id")}
        },
        "update_task": {
            "success": True,
            "data": {
                "id": int(params.get("task_id", 1)),
                "title": params.get("title", "Updated Task"),
                "priority": params.get("priority", "Medium"),
            }
        },
    }.get(tool, {"success": False, "error": {"code": "unknown_tool"}}))

    return server


@pytest.fixture
def mock_session_factory():
    """Create mock session factory."""
    return MagicMock()


@pytest.fixture
def sample_context():
    """Create sample agent context."""
    return AgentContext.from_request(
        user_id="123",
        conversation_id="conv-456",
        messages=[
            {"role": "user", "content": "Show my tasks"},
            {"role": "assistant", "content": "Here are your tasks..."},
        ]
    )


@pytest.fixture
def empty_context():
    """Create context with no history."""
    return AgentContext.from_request(
        user_id="123",
        conversation_id="conv-789",
        messages=[]
    )


@pytest.fixture
def sample_tasks():
    """Sample task data for testing."""
    return [
        {"id": 1, "title": "Buy milk", "completed": False, "priority": "Medium"},
        {"id": 2, "title": "Call mom", "completed": False, "priority": "High"},
        {"id": 3, "title": "Buy groceries", "completed": True, "priority": "Low"},
    ]
