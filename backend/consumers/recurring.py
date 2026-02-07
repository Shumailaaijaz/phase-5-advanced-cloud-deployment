"""Recurring Task Consumer

Subscribes to task-events topic, listens for task.completed events.
When a completed task has a recurrence_rule, creates the next occurrence.

Runs as a separate process/deployment with Dapr sidecar.
Dapr invokes POST /task-events when events arrive.
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlmodel import Session, create_engine, select

from models.user import Task
from events.emitter import emit_event

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

# Track processed event IDs for idempotency
_processed_events: set = set()
MAX_PROCESSED_CACHE = 10000


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Recurring task consumer starting...")
    yield
    logger.info("Recurring task consumer shutting down...")


app = FastAPI(title="Recurring Task Consumer", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/dapr/subscribe")
async def subscribe():
    """Tell Dapr which topics this consumer subscribes to."""
    return [
        {
            "pubsubname": "task-pubsub",
            "topic": "task-events",
            "route": "/task-events",
        }
    ]


@app.post("/task-events")
async def handle_task_event(request: Request):
    """Process task events from Kafka via Dapr."""
    body = await request.json()

    # Dapr wraps the event in a CloudEvents envelope
    data = body.get("data", body)
    event_id = data.get("event_id", "")
    event_type = data.get("event_type", "")

    # Idempotency check
    if event_id in _processed_events:
        logger.info(f"Skipping duplicate event: {event_id}")
        return {"status": "DUPLICATE"}

    if event_type != "task.completed":
        return {"status": "IGNORED"}

    task_id = data.get("task_id")
    user_id = data.get("user_id")
    task_data = data.get("data", {})

    recurrence_rule = task_data.get("recurrence_rule")
    if not recurrence_rule:
        return {"status": "NO_RECURRENCE"}

    recurrence_depth = task_data.get("recurrence_depth", 0)
    if recurrence_depth >= 1000:
        logger.warning(f"Max recurrence depth reached for task {task_id}")
        return {"status": "MAX_DEPTH"}

    # Create next occurrence
    try:
        if engine is None:
            logger.error("DATABASE_URL not configured")
            return {"status": "ERROR"}

        with Session(engine) as session:
            parent_task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if parent_task is None:
                logger.warning(f"Parent task {task_id} not found")
                return {"status": "NOT_FOUND"}

            # Calculate next due date
            next_due = _advance_due_date(parent_task.due_date, recurrence_rule)

            new_task = Task(
                user_id=user_id,
                title=parent_task.title,
                description=parent_task.description,
                priority=parent_task.priority,
                due_date=next_due,
                recurrence_rule=recurrence_rule,
                recurrence_parent_id=parent_task.id,
                recurrence_depth=recurrence_depth + 1,
                reminder_minutes=parent_task.reminder_minutes,
                completed=False,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )
            session.add(new_task)
            session.commit()
            session.refresh(new_task)

            logger.info(f"Created recurring task {new_task.id} from parent {task_id} (depth={new_task.recurrence_depth})")

            # Emit event for the new task (after commit)
            emit_event(
                event_type="task.created",
                user_id=user_id,
                task_id=new_task.id,
                data={
                    "title": new_task.title,
                    "recurrence_rule": recurrence_rule,
                    "recurrence_depth": new_task.recurrence_depth,
                },
            )

        # Mark as processed
        _processed_events.add(event_id)
        if len(_processed_events) > MAX_PROCESSED_CACHE:
            _processed_events.clear()

        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(f"Error processing recurring task event: {e}")
        return {"status": "ERROR"}


def _advance_due_date(current_due, rule: str):
    """Advance due date by recurrence interval."""
    if current_due is None:
        return datetime.now(timezone.utc)

    if isinstance(current_due, str):
        current_due = datetime.fromisoformat(current_due)

    if rule == "daily":
        return current_due + timedelta(days=1)
    elif rule == "weekly":
        return current_due + timedelta(weeks=1)
    elif rule == "monthly":
        # Add roughly one month
        month = current_due.month % 12 + 1
        year = current_due.year + (1 if current_due.month == 12 else 0)
        day = min(current_due.day, 28)  # Safe for all months
        return current_due.replace(year=year, month=month, day=day)
    else:
        return current_due + timedelta(days=1)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
