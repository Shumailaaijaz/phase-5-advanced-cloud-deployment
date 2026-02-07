"""MCP Tool Parameter Schemas

Input validation models for all MCP tool parameters.
"""

from typing import Optional
from pydantic import BaseModel, field_validator
import re


VALID_PRIORITIES = ["Low", "Medium", "High"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class AddTaskParams(BaseModel):
    """Parameters for add_task tool."""

    user_id: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v

    @field_validator("title")
    @classmethod
    def title_valid(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Title cannot be empty")
        if len(v) > 255:
            raise ValueError("Title cannot exceed 255 characters")
        return v.strip()

    @field_validator("description")
    @classmethod
    def description_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not DATE_PATTERN.match(v):
            raise ValueError("Due date must be in YYYY-MM-DD format")
        return v


class ListTasksParams(BaseModel):
    """Parameters for list_tasks tool."""

    user_id: str

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v


class CompleteTaskParams(BaseModel):
    """Parameters for complete_task tool."""

    task_id: str
    user_id: str

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v

    @field_validator("task_id")
    @classmethod
    def task_id_valid(cls, v: str) -> str:
        try:
            task_int = int(v)
            if task_int <= 0:
                raise ValueError("task_id must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("task_id must be a valid positive integer")
        return v


class DeleteTaskParams(BaseModel):
    """Parameters for delete_task tool."""

    task_id: str
    user_id: str

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v

    @field_validator("task_id")
    @classmethod
    def task_id_valid(cls, v: str) -> str:
        try:
            task_int = int(v)
            if task_int <= 0:
                raise ValueError("task_id must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("task_id must be a valid positive integer")
        return v


class UpdateTaskParams(BaseModel):
    """Parameters for update_task tool."""

    task_id: str
    user_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v

    @field_validator("task_id")
    @classmethod
    def task_id_valid(cls, v: str) -> str:
        try:
            task_int = int(v)
            if task_int <= 0:
                raise ValueError("task_id must be a positive integer")
        except (ValueError, TypeError):
            raise ValueError("task_id must be a valid positive integer")
        return v

    @field_validator("title")
    @classmethod
    def title_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v.strip():
                raise ValueError("Title cannot be empty")
            if len(v) > 255:
                raise ValueError("Title cannot exceed 255 characters")
            return v.strip()
        return v

    @field_validator("description")
    @classmethod
    def description_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v) > 1000:
            raise ValueError("Description cannot exceed 1000 characters")
        return v

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v

    @field_validator("due_date")
    @classmethod
    def due_date_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not DATE_PATTERN.match(v):
            raise ValueError("Due date must be in YYYY-MM-DD format")
        return v

    def has_update_fields(self) -> bool:
        """Check if at least one update field is provided."""
        return any([
            self.title is not None,
            self.description is not None,
            self.priority is not None,
            self.due_date is not None,
            self.completed is not None,
        ])
