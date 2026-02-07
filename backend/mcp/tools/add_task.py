"""add_task MCP Tool

Creates a new task for the user.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import AddTaskParams
from mcp.schemas.responses import ToolResponse, TaskData
from mcp.crud.task import create_task

logger = logging.getLogger(__name__)


def add_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Create a new task for the user.

    Args:
        params: Raw parameters dict from agent
        get_session: Factory to create fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse with created TaskData or error
    """
    logger.info(f"add_task invoked for user_id={user_id_int}")

    # Validate parameters
    try:
        validated = AddTaskParams(**params)
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

    # Create task in database
    try:
        session = get_session()
        task = create_task(session, user_id_int, validated)
        task_data = TaskData.from_task(task, validated.user_id)
        logger.info(f"add_task success: task_id={task.id}")
        return ToolResponse.ok(task_data.model_dump())
    except Exception as e:
        logger.error(f"add_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to create task",
            details={"error": str(e)}
        )
