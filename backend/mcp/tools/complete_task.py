"""complete_task MCP Tool

Marks a task as completed. Idempotent.
"""

import logging
from typing import Callable
from datetime import datetime
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import CompleteTaskParams
from mcp.schemas.responses import ToolResponse
from mcp.crud.task import get_task_by_id_and_user

logger = logging.getLogger(__name__)


def complete_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Mark a task as completed. Idempotent - completing an already-completed task succeeds.

    Args:
        params: Raw parameters dict from agent
        get_session: Factory to create fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse with partial TaskData or error
    """
    logger.info(f"complete_task invoked for user_id={user_id_int}")

    # Validate parameters
    try:
        validated = CompleteTaskParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        return ToolResponse.fail(
            code="invalid_input",
            message=error.get("msg", "Validation error"),
            details={"field": str(error.get("loc", ["unknown"])[0])}
        )

    task_id = int(validated.task_id)

    # Lookup and update task
    try:
        session = get_session()
        task = get_task_by_id_and_user(session, task_id, user_id_int)

        if task is None:
            logger.warning(f"complete_task not_found: task_id={task_id}")
            return ToolResponse.fail(
                code="not_found",
                message="Task not found",
                details={"task_id": validated.task_id}
            )

        # Idempotent: if already completed, still return success
        if not task.completed:
            task.completed = True
            task.updated_at = datetime.utcnow()
            session.add(task)
            session.commit()
            session.refresh(task)

        result = {
            "id": task.id,
            "title": task.title,
            "completed": task.completed,
            "updated_at": task.updated_at.isoformat() + "Z" if isinstance(task.updated_at, datetime) else str(task.updated_at),
        }

        logger.info(f"complete_task success: task_id={task.id}")
        return ToolResponse.ok(result)
    except Exception as e:
        logger.error(f"complete_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to complete task",
            details={"error": str(e)}
        )
