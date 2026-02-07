"""list_tasks MCP Tool

Retrieves all tasks for a user.
"""

import logging
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import ListTasksParams
from mcp.schemas.responses import ToolResponse, TaskData, ListTasksData
from mcp.crud.task import get_tasks_for_user

logger = logging.getLogger(__name__)


def list_tasks(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """List all tasks for the user, ordered by creation time (newest first).

    Args:
        params: Raw parameters dict from agent
        get_session: Factory to create fresh DB session
        user_id_int: Authenticated user ID (integer)

    Returns:
        ToolResponse with ListTasksData or error
    """
    logger.info(f"list_tasks invoked for user_id={user_id_int}")

    # Validate parameters
    try:
        validated = ListTasksParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        return ToolResponse.fail(
            code="invalid_input",
            message=error.get("msg", "Validation error"),
            details={"field": str(error.get("loc", ["unknown"])[0])}
        )

    # Query tasks from database
    try:
        session = get_session()
        tasks = get_tasks_for_user(session, user_id_int)

        task_data_list = [
            TaskData.from_task(task, validated.user_id)
            for task in tasks
        ]

        result = ListTasksData(tasks=task_data_list, total=len(task_data_list))
        logger.info(f"list_tasks success: count={result.total}")
        return ToolResponse.ok(result.model_dump())
    except Exception as e:
        logger.error(f"list_tasks error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to retrieve tasks",
            details={"error": str(e)}
        )
