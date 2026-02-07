"""MCP CRUD Module"""

from mcp.crud.task import (
    create_task,
    get_tasks_for_user,
    get_task_by_id_and_user,
    update_task,
    delete_task,
)

__all__ = [
    "create_task",
    "get_tasks_for_user",
    "get_task_by_id_and_user",
    "update_task",
    "delete_task",
]
