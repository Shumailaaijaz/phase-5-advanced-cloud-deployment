"""update_task MCP Tool

Modifies task attributes.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import UpdateTaskParams
from mcp.schemas.responses import ToolResponse, TaskData
from mcp.crud.task import get_task_by_id_and_user, update_task as crud_update

logger = logging.getLogger(__name__)


def update_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Update task attributes. Only provided fields are modified.

    Args:
        params: Raw parameters dict from agent
        get_session: Factory to create fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse with updated TaskData or error
    """
    logger.info(f"update_task invoked for user_id={user_id_int}")

    # Validate parameters
    try:
        validated = UpdateTaskParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        field = error.get("loc", ["unknown"])[0]
        msg = error.get("msg", "Validation error")

        if "priority" in str(field).lower() or "priority" in msg.lower():
            return ToolResponse.fail(
                code="invalid_priority",
                message="Priority must be one of: Low, Medium, High",
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

    # Check at least one update field is provided
    if not validated.has_update_fields():
        return ToolResponse.fail(
            code="invalid_input",
            message="At least one field must be provided for update",
            details={}
        )

    task_id = int(validated.task_id)

    # Lookup and update task
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
        task_data = TaskData.from_task(updated_task, validated.user_id)

        logger.info(f"update_task success: task_id={task_id}")
        return ToolResponse.ok(task_data.model_dump())
    except Exception as e:
        logger.error(f"update_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to update task",
            details={"error": str(e)}
        )
