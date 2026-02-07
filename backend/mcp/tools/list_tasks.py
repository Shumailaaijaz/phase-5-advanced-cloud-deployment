"""list_tasks MCP Tool

Retrieves tasks for a user with search, filtering, sorting, and pagination.
"""

import logging
import math
from typing import Callable
from pydantic import ValidationError
from sqlmodel import Session

from mcp.schemas.params import ListTasksParams
from mcp.schemas.responses import ToolResponse, TaskData, ListTasksData
from mcp.crud.task import get_tasks_filtered, _get_tags_for_task

logger = logging.getLogger(__name__)


def list_tasks(params: dict, get_session: Callable[[], Session], user_id_int: int) -> ToolResponse:
    """List tasks with optional search, filters, sort, and pagination."""
    logger.info(f"list_tasks invoked for user_id={user_id_int}")

    try:
        validated = ListTasksParams(**params)
    except ValidationError as e:
        error = e.errors()[0]
        return ToolResponse.fail(
            code="invalid_input",
            message=error.get("msg", "Validation error"),
            details={"field": str(error.get("loc", ["unknown"])[0])}
        )

    try:
        session = get_session()
        tasks, total_count = get_tasks_filtered(session, user_id_int, validated)

        page = validated.page or 1
        page_size = validated.page_size or 20
        total_pages = max(1, math.ceil(total_count / page_size))

        task_data_list = []
        for task in tasks:
            tags = _get_tags_for_task(session, task.id)
            task_data_list.append(TaskData.from_task(task, validated.user_id, tags=tags))

        result = ListTasksData(
            tasks=task_data_list,
            total=total_count,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
        logger.info(f"list_tasks success: count={total_count}, page={page}/{total_pages}")
        return ToolResponse.ok(result.model_dump())
    except Exception as e:
        logger.error(f"list_tasks error: {e}")
        return ToolResponse.fail(
            code="processing_error",
            message="Failed to retrieve tasks",
            details={"error": str(e)}
        )
