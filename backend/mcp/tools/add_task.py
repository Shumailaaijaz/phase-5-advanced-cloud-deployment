"""add_task MCP Tool

Creates a new task for the user.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import AddTaskParams
from mcp.schemas.responses import ToolResponse, TaskData
from mcp.crud.task import create_task, _get_tags_for_task
from events.emitter import emit_event

logger = logging.getLogger(__name__)


def add_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Create a new task for the user."""
    logger.info(f"add_task invoked for user_id={user_id_int}")

    try:
        validated = AddTaskParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        field = error.get("loc", ["unknown"])[0]
        msg = error.get("msg", "Validation error")

        if "priority" in str(field).lower() or "priority" in msg.lower():
            return ToolResponse.fail(
                code="invalid_priority",
                message="Priority must be one of: P1, P2, P3, P4",
                details={"field": "priority", "value": params.get("priority")}
            )
        if "due_date" in str(field).lower() or "YYYY-MM-DD" in msg:
            return ToolResponse.fail(
                code="invalid_date",
                message="Due date must be in YYYY-MM-DD format",
                details={"field": "due_date"}
            )

        return ToolResponse.fail(
            code="invalid_input",
            message=msg,
            details={"field": str(field)}
        )

    try:
        session = get_session()
        task = create_task(session, user_id_int, validated)
        tags = _get_tags_for_task(session, task.id)
        task_data = TaskData.from_task(task, validated.user_id, tags=tags)

        # Emit event AFTER commit
        emit_event("task.created", user_id_int, task.id, {
            "title": task.title,
            "priority": task.priority,
            "tags": tags,
            "recurrence_rule": task.recurrence_rule,
        })

        logger.info(f"add_task success: task_id={task.id}")
        return ToolResponse.ok(task_data.model_dump())
    except Exception as e:
        logger.error(f"add_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to create task",
            details={"error": str(e)}
        )
