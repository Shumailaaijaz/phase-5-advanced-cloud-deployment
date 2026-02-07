"""Audit Logger Consumer

Subscribes to task-events topic, logs all events in structured JSON format.
Provides event trail for debugging and judge demo.
Loki-compatible structured logging to stdout.

Runs as a separate process/deployment with Dapr sidecar.
Dapr invokes POST /task-events when events arrive.
"""

import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Raw JSON output for Loki
)

# Separate structured logger for audit events
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Audit logger consumer starting...")
    yield
    logger.info("Audit logger consumer shutting down...")


app = FastAPI(title="Audit Logger Consumer", lifespan=lifespan)


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
    """Log all task events in structured JSON format."""
    body = await request.json()

    # Dapr wraps the event in a CloudEvents envelope
    data = body.get("data", body)
    event_id = data.get("event_id", "unknown")
    event_type = data.get("event_type", "unknown")
    user_id = data.get("user_id")
    task_id = data.get("task_id")
    timestamp = data.get("timestamp", "")

    # Structured JSON audit log entry
    audit_entry = {
        "audit": True,
        "event_id": event_id,
        "event_type": event_type,
        "user_id": user_id,
        "task_id": task_id,
        "timestamp": timestamp,
        "data": data.get("data", {}),
        "schema_version": data.get("schema_version", "1.0"),
    }

    # Log structured JSON to stdout (Loki-compatible)
    audit_logger.info(json.dumps(audit_entry))

    return {"status": "LOGGED"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)
