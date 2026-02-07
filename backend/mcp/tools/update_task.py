"""update_task MCP Tool

Modifies task attributes.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import UpdateTaskParams
from mcp.schemas.responses import ToolResponse, TaskData
from mcp.crud.task import get_task_by_id_and_user, update_task as crud_update, _get_tags_for_task
from events.emitter import emit_event

logger = logging.getLogger(__name__)


def update_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Update task attributes. Only provided fields are modified."""
    logger.info(f"update_task invoked for user_id={user_id_int}")

    try:
        validated = UpdateTaskParams(**params)
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

    if not validated.has_update_fields():
        return ToolResponse.fail(
            code="invalid_input",
            message="At least one field must be provided for update",
            details={}
        )

    task_id = int(validated.task_id)

    try:
        session = get_session()
        task = get_task_by_id_and_user(session, task_id, user_id_int)

        if task is None:
            logger.warning(f"update_task not_found: task_id={task_id}")
            return ToolResponse.fail(
                code="not_found",
                message="Task not found",
                details={"task_id": validated.task_id}
            )

        updated_task = crud_update(session, task, validated)
        tags = _get_tags_for_task(session, updated_task.id)
        task_data = TaskData.from_task(updated_task, validated.user_id, tags=tags)

        # Emit event AFTER commit
        emit_event("task.updated", user_id_int, task_id, {
            "title": updated_task.title,
            "priority": updated_task.priority,
            "completed": updated_task.completed,
        })

        logger.info(f"update_task success: task_id={task_id}")
        return ToolResponse.ok(task_data.model_dump())
    except Exception as e:
        logger.error(f"update_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to update task",
            details={"error": str(e)}
        )
