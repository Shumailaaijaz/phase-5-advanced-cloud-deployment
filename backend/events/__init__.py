"""Event-Driven Architecture Module

Provides domain event emission with dual transport (Dapr HTTP / direct Kafka).
"""

from events.emitter import emit_event
from events.schemas import TaskEvent

__all__ = ["emit_event", "TaskEvent"]
