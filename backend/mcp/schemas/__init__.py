"""MCP Schemas Module"""

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
    "ToolResponse",
    "ToolError",
    "TaskData",
    "ListTasksData",
    "DeleteTaskData",
    "AddTaskParams",
    "ListTasksParams",
    "CompleteTaskParams",
    "DeleteTaskParams",
    "UpdateTaskParams",
]
