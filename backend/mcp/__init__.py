"""MCP Task Tools Module

Exposes stateless task management tools for AI agent consumption.
"""

from mcp.tools import (
    add_task,
    list_tasks,
    complete_task,
    delete_task,
    update_task,
)
from mcp.schemas.responses import (
    ToolResponse,
    ToolError,
    TaskData,
    ListTasksData,
    DeleteTaskData,
)
from mcp.schemas.params import (
    AddTaskParams,
    ListTasksParams,
    CompleteTaskParams,
    DeleteTaskParams,
    UpdateTaskParams,
)

__all__ = [
    # Tools
    "add_task",
    "list_tasks",
    "complete_task",
    "delete_task",
    "update_task",
    # Response schemas
    "ToolResponse",
    "ToolError",
    "TaskData",
    "ListTasksData",
    "DeleteTaskData",
    # Parameter schemas
    "AddTaskParams",
    "ListTasksParams",
    "CompleteTaskParams",
    "DeleteTaskParams",
    "UpdateTaskParams",
]
