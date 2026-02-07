"""Event Emitter — fire-and-forget with 3x retry

IMPORTANT: Only call emit_event() AFTER session.commit() succeeds.
Event emission failures are logged but never raise — CRUD operations must not break.
"""

import asyncio
import logging
from typing import Dict, Any

from events.schemas import TaskEvent
from events.transport import get_transport

logger = logging.getLogger(__name__)

TOPIC = "task-events"
MAX_RETRIES = 3


async def _publish_with_retry(event: Dict[str, Any]) -> None:
    """Attempt to publish with exponential backoff retry."""
    transport = get_transport()
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            success = await transport.publish(TOPIC, event)
            if success:
                return
        except Exception as e:
            logger.warning(f"Publish attempt {attempt}/{MAX_RETRIES} failed: {e}")
        if attempt < MAX_RETRIES:
            await asyncio.sleep(0.5 * attempt)  # 0.5s, 1s backoff

    logger.error(f"Event publish failed after {MAX_RETRIES} retries: {event.get('event_type')}")


def emit_event(
    event_type: str,
    user_id: int,
    task_id: int,
    data: Dict[str, Any],
) -> None:
    """Fire-and-forget event emission. Safe to call — never raises.

    Args:
        event_type: e.g. "task.created", "task.updated", "task.completed", "task.deleted"
        user_id: Owner's user ID
        task_id: The task ID this event relates to
        data: Event payload (task fields, changes, etc.)
    """
    try:
        event = TaskEvent(
            event_type=event_type,
            user_id=user_id,
            task_id=task_id,
            data=data,
        )
        event_dict = event.to_dict()
        logger.info(f"Event emitting: {event_type} for task_id={task_id}")

        # Schedule async publish — fire and forget
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_publish_with_retry(event_dict))
        except RuntimeError:
            # No running event loop — run synchronously in a new loop
            asyncio.run(_publish_with_retry(event_dict))

    except Exception as e:
        # Never let event emission break CRUD
        logger.error(f"Event emission error (swallowed): {e}")
