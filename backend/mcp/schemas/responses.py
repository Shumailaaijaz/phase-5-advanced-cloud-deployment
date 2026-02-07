"""MCP Tool Response Schemas

Standardized response wrappers for all MCP tool invocations.
"""

from typing import Optional, Any, List
from pydantic import BaseModel
from datetime import datetime


class ToolError(BaseModel):
    """Structured error information for failed tool calls."""

    code: str
    message: str
    details: Optional[dict] = None


class TaskData(BaseModel):
    """Serialized task data for tool responses."""

    id: int
    user_id: str
    title: str
    description: Optional[str] = None
    completed: bool
    priority: str
    due_date: Optional[str] = None
    created_at: str
    updated_at: str

    @classmethod
    def from_task(cls, task: Any, user_id: str) -> "TaskData":
        """Create TaskData from a Task model instance."""
        return cls(
            id=task.id,
            user_id=user_id,
            title=task.title,
            description=task.description,
            completed=task.completed,
            priority=task.priority,
            due_date=task.due_date,
            created_at=task.created_at.isoformat() + "Z" if isinstance(task.created_at, datetime) else str(task.created_at),
            updated_at=task.updated_at.isoformat() + "Z" if isinstance(task.updated_at, datetime) else str(task.updated_at),
        )


class ListTasksData(BaseModel):
    """Response payload for list_tasks tool."""

    tasks: List[TaskData]
    total: int


class DeleteTaskData(BaseModel):
    """Response payload for delete_task tool."""

    deleted: bool
    task_id: str


class ToolResponse(BaseModel):
    """Standardized wrapper for all tool responses.

    Invariant: Exactly one of `data` or `error` is present.
    """

    success: bool
    data: Optional[Any] = None
    error: Optional[ToolError] = None

    @classmethod
    def ok(cls, data: Any) -> "ToolResponse":
        """Create a successful response."""
        return cls(success=True, data=data)

    @classmethod
    def fail(cls, code: str, message: str, details: Optional[dict] = None) -> "ToolResponse":
        """Create a failed response."""
        return cls(
            success=False,
            error=ToolError(code=code, message=message, details=details)
        )
