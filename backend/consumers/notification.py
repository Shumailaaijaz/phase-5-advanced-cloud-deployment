"""Notification Service Consumer

Subscribes to reminders topic, listens for reminder.due events.
Processes reminder delivery: logs the reminder and marks reminder_sent=True in DB.
Tracks event_id for idempotency.

Runs as a separate process/deployment with Dapr sidecar.
Dapr invokes POST /reminders when events arrive.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from sqlmodel import Session, create_engine, select

from models.user import Task

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

DATABASE_URL = os.getenv("DATABASE_URL", "")
engine = create_engine(DATABASE_URL) if DATABASE_URL else None

# Track processed event IDs for idempotency
_processed_events: set = set()
MAX_PROCESSED_CACHE = 10000


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Notification consumer starting...")
    yield
    logger.info("Notification consumer shutting down...")


app = FastAPI(title="Notification Service Consumer", lifespan=lifespan)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/dapr/subscribe")
async def subscribe():
    """Tell Dapr which topics this consumer subscribes to."""
    return [
        {
            "pubsubname": "task-pubsub",
            "topic": "reminders",
            "route": "/reminders",
        }
    ]


@app.post("/reminders")
async def handle_reminder_event(request: Request):
    """Process reminder events from Kafka via Dapr."""
    body = await request.json()

    # Dapr wraps the event in a CloudEvents envelope
    data = body.get("data", body)
    event_id = data.get("event_id", "")
    event_type = data.get("event_type", "")

    # Idempotency check
    if event_id in _processed_events:
        logger.info(f"Skipping duplicate reminder event: {event_id}")
        return {"status": "DUPLICATE"}

    if event_type != "reminder.due":
        return {"status": "IGNORED"}

    task_id = data.get("task_id")
    user_id = data.get("user_id")
    task_title = data.get("task_title", "Unknown Task")
    due_date = data.get("due_date", "")

    try:
        if engine is None:
            logger.error("DATABASE_URL not configured")
            return {"status": "ERROR"}

        with Session(engine) as session:
            task = session.exec(
                select(Task).where(Task.id == task_id, Task.user_id == user_id)
            ).first()

            if task is None:
                logger.warning(f"Task {task_id} not found for reminder")
                return {"status": "NOT_FOUND"}

            if task.reminder_sent:
                logger.info(f"Reminder already sent for task {task_id}")
                return {"status": "ALREADY_SENT"}

            # Mark reminder as sent
            task.reminder_sent = True
            session.add(task)
            session.commit()

            logger.info(
                f"REMINDER DELIVERED: Task '{task_title}' (id={task_id}) "
                f"for user {user_id}, due at {due_date}"
            )

        # Mark as processed
        _processed_events.add(event_id)
        if len(_processed_events) > MAX_PROCESSED_CACHE:
            _processed_events.clear()

        return {"status": "SUCCESS"}

    except Exception as e:
        logger.error(f"Error processing reminder event: {e}")
        return {"status": "ERROR"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
