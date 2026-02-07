"""Domain Event Schemas"""

import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field, asdict
from typing import Any, Dict


@dataclass
class TaskEvent:
    """Schema for task domain events published to Kafka."""

    event_type: str  # task.created, task.updated, task.completed, task.deleted
    user_id: int
    task_id: int
    data: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReminderEvent:
    """Schema for reminder events."""

    event_type: str  # reminder.due
    user_id: int
    task_id: int
    task_title: str
    due_date: str
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    schema_version: str = "1.0"
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
