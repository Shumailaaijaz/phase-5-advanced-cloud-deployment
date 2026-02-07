"""MCP Server Module

Registers task management tools with the MCP SDK for agent consumption.
"""

import logging
from typing import Callable, Any, Dict

from sqlmodel import Session

from mcp.tools import (
    add_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
)

logger = logging.getLogger(__name__)


# Tool definitions matching contracts/mcp-tools.md
TOOL_DEFINITIONS = [
    {
        "name": "add_task",
        "description": "Create a new task for the user. Returns the created task with its ID.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ID of the user creating the task"
                },
                "title": {
                    "type": "string",
                    "description": "Task title (1-255 characters)",
                    "minLength": 1,
                    "maxLength": 255
                },
                "description": {
                    "type": "string",
                    "description": "Optional task description",
                    "maxLength": 1000
                },
                "priority": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                    "description": "Priority level (default: Medium)"
                },
                "due_date": {
                    "type": "string",
                    "description": "Due date in YYYY-MM-DD format"
                }
            },
            "required": ["user_id", "title"]
        }
    },
    {
        "name": "list_tasks",
        "description": "List all tasks for the user, ordered by creation time (newest first)",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "ID of the user whose tasks to list"
                }
            },
            "required": ["user_id"]
        }
    },
    {
        "name": "complete_task",
        "description": "Mark a task as completed. Idempotent - completing an already-completed task succeeds.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to complete"
                },
                "user_id": {
                    "type": "string",
                    "description": "ID of the user (for ownership verification)"
                }
            },
            "required": ["task_id", "user_id"]
        }
    },
    {
        "name": "delete_task",
        "description": "Permanently delete a task. Cannot be undone.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to delete"
                },
                "user_id": {
                    "type": "string",
                    "description": "ID of the user (for ownership verification)"
                }
            },
            "required": ["task_id", "user_id"]
        }
    },
    {
        "name": "update_task",
        "description": "Update task attributes. Only provided fields are modified.",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to update"
                },
                "user_id": {
                    "type": "string",
                    "description": "ID of the user (for ownership verification)"
                },
                "title": {
                    "type": "string",
                    "description": "New title (1-255 characters)",
                    "minLength": 1,
                    "maxLength": 255
                },
                "description": {
                    "type": "string",
                    "description": "New description",
                    "maxLength": 1000
                },
                "priority": {
                    "type": "string",
                    "enum": ["Low", "Medium", "High"],
                    "description": "New priority level"
                },
                "due_date": {
                    "type": "string",
                    "description": "New due date in YYYY-MM-DD format"
                },
                "completed": {
                    "type": "boolean",
                    "description": "New completion status"
                }
            },
            "required": ["task_id", "user_id"]
        }
    }
]


# Tool function registry
TOOL_HANDLERS = {
    "add_task": add_task,
    "list_tasks": list_tasks,
    "complete_task": complete_task,
    "delete_task": delete_task,
    "update_task": update_task,
}


def get_tool_definitions() -> list:
    """Get all tool definitions for agent registration.

    Returns:
        List of tool definition dicts matching OpenAI function calling format
    """
    return TOOL_DEFINITIONS


def invoke_tool(
    tool_name: str,
    params: Dict[str, Any],
    get_session: Callable[[], Session],
    user_id_int: int
) -> Dict[str, Any]:
    """Invoke an MCP tool by name.

    Args:
        tool_name: Name of the tool to invoke
        params: Tool parameters
        get_session: Session factory for fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse as dict

    Raises:
        ValueError: If tool_name is not registered
    """
    handler = TOOL_HANDLERS.get(tool_name)
    if handler is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    logger.info(f"Invoking tool: {tool_name}")
    response = handler(params, get_session, user_id_int)
    return response.model_dump()


class MCPToolServer:
    """MCP Tool Server for agent integration.

    Provides tool definitions and invocation interface.
    """

    def __init__(self, session_factory: Callable[[], Session]):
        """Initialize MCP server with session factory.

        Args:
            session_factory: Factory to create fresh DB sessions
        """
        self._session_factory = session_factory

    @property
    def tools(self) -> list:
        """Get tool definitions."""
        return get_tool_definitions()

    def call(self, tool_name: str, params: Dict[str, Any], user_id_int: int) -> Dict[str, Any]:
        """Call a tool with the given parameters.

        Args:
            tool_name: Name of the tool
            params: Tool parameters
            user_id_int: Authenticated user ID

        Returns:
            Tool response as dict
        """
        return invoke_tool(tool_name, params, self._session_factory, user_id_int)
