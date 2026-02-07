"""delete_task MCP Tool

Permanently removes a task.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import DeleteTaskParams
from mcp.schemas.responses import ToolResponse, DeleteTaskData
from mcp.crud.task import get_task_by_id_and_user, delete_task as crud_delete

logger = logging.getLogger(__name__)


def delete_task(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """Permanently delete a task. Cannot be undone.

    Args:
        params: Raw parameters dict from agent
        get_session: Factory to create fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse with DeleteTaskData or error
    """
    logger.info(f"delete_task invoked for user_id={user_id_int}")

    # Validate parameters
    try:
        validated = DeleteTaskParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        return ToolResponse.fail(
            code="invalid_input",
            message=error.get("msg", "Validation error"),
            details={"field": str(error.get("loc", ["unknown"])[0])}
        )

    task_id = int(validated.task_id)

    # Lookup and delete task
    try:
        session = get_session()
        task = get_task_by_id_and_user(session, task_id, user_id_int)

        if task is None:
            logger.warning(f"delete_task not_found: task_id={task_id}")
            return ToolResponse.fail(
                code="not_found",
                message="Task not found",
                details={"task_id": validated.task_id}
            )

        crud_delete(session, task)

        result = DeleteTaskData(deleted=True, task_id=validated.task_id)
        logger.info(f"delete_task success: task_id={validated.task_id}")
        return ToolResponse.ok(result.model_dump())
    except Exception as e:
        logger.error(f"delete_task error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to delete task",
            details={"error": str(e)}
        )
