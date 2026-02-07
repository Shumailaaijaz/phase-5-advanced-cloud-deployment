"""MCP Tool Parameter Schemas

Input validation models for all MCP tool parameters.
"""

from typing import Optional, List
from pydantic import BaseModel, field_validator
import re


VALID_PRIORITIES = ["P1", "P2", "P3", "P4"]
VALID_RECURRENCE = ["daily", "weekly", "monthly"]
VALID_SORT_FIELDS = ["created_at", "updated_at", "due_date", "priority", "title"]
VALID_SORT_ORDERS = ["asc", "desc"]
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2})?")


class AddTaskParams(BaseModel):
    """Parameters for add_task tool."""

    user_id: str
    title: str
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes: Optional[int] = None

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
            raise ValueError("Due date must be in YYYY-MM-DD or ISO 8601 format")
        return v

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags per task")
            cleaned = []
            for tag in v:
                tag = tag.strip().lower()
                if not tag:
                    raise ValueError("Tag name cannot be empty")
                if len(tag) > 50:
                    raise ValueError("Tag name cannot exceed 50 characters")
                cleaned.append(tag)
            return cleaned
        return v

    @field_validator("recurrence_rule")
    @classmethod
    def recurrence_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_RECURRENCE:
            raise ValueError(f"Recurrence rule must be one of: {', '.join(VALID_RECURRENCE)}")
        return v

    @field_validator("reminder_minutes")
    @classmethod
    def reminder_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Reminder minutes must be >= 0")
        return v


class ListTasksParams(BaseModel):
    """Parameters for list_tasks tool."""

    user_id: str
    search: Optional[str] = None
    priority: Optional[str] = None
    tag: Optional[str] = None
    completed: Optional[bool] = None
    due_before: Optional[str] = None
    due_after: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: Optional[str] = None
    page: Optional[int] = None
    page_size: Optional[int] = None

    @field_validator("user_id")
    @classmethod
    def user_id_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("user_id cannot be empty")
        return v

    @field_validator("priority")
    @classmethod
    def priority_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"Priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v

    @field_validator("sort_by")
    @classmethod
    def sort_by_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SORT_FIELDS:
            raise ValueError(f"sort_by must be one of: {', '.join(VALID_SORT_FIELDS)}")
        return v

    @field_validator("sort_order")
    @classmethod
    def sort_order_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_SORT_ORDERS:
            raise ValueError(f"sort_order must be one of: {', '.join(VALID_SORT_ORDERS)}")
        return v

    @field_validator("page")
    @classmethod
    def page_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 1:
            raise ValueError("Page must be >= 1")
        return v

    @field_validator("page_size")
    @classmethod
    def page_size_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and (v < 1 or v > 100):
            raise ValueError("Page size must be between 1 and 100")
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
    tags: Optional[List[str]] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes: Optional[int] = None

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
            raise ValueError("Due date must be in YYYY-MM-DD or ISO 8601 format")
        return v

    @field_validator("tags")
    @classmethod
    def tags_valid(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is not None:
            if len(v) > 10:
                raise ValueError("Maximum 10 tags per task")
            return [t.strip().lower() for t in v if t.strip()]
        return v

    @field_validator("recurrence_rule")
    @classmethod
    def recurrence_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_RECURRENCE:
            raise ValueError(f"Recurrence rule must be one of: {', '.join(VALID_RECURRENCE)}")
        return v

    @field_validator("reminder_minutes")
    @classmethod
    def reminder_valid(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and v < 0:
            raise ValueError("Reminder minutes must be >= 0")
        return v

    def has_update_fields(self) -> bool:
        """Check if at least one update field is provided."""
        return any([
            self.title is not None,
            self.description is not None,
            self.priority is not None,
            self.due_date is not None,
            self.completed is not None,
            self.tags is not None,
            self.recurrence_rule is not None,
            self.reminder_minutes is not None,
        ])
