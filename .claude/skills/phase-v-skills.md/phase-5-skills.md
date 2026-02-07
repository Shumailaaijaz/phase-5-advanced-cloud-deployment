# Phase V Skills — Advanced Cloud Deployment

## Overview

Phase V extends the Todo AI Chatbot from a locally-deployed monolith (Phases III-IV) into a production-grade, event-driven distributed system. This skills catalog covers 12 specialized skills spanning advanced feature implementation, Kafka event streaming, Dapr distributed runtime integration, cloud Kubernetes deployment (Oracle OKE primary, AKS/GKE fallback), CI/CD automation, and observability.

All skills build upon Phase III foundations (FastAPI + SQLModel + MCP + Neon PostgreSQL) and Phase IV infrastructure (Minikube + Helm + Docker Desktop on WSL2). Skills follow the Agentic Dev Stack workflow: Write spec → Generate plan → Break into tasks → Implement via Claude Code.

**Key Phase V principles:**
- Event-first design: every feature emits domain events for Kafka consumption
- Dapr abstraction: application code talks to Dapr HTTP APIs, never directly to Kafka/state stores
- Cloud-portable: same Helm charts work on Minikube, OKE, AKS, and GKE with values overrides
- Smallest viable diff: extend existing Phase III/IV code, never rewrite

---

## Core Skills Catalog

### 1. Schema Migration Extensions

**Purpose**: Extend the existing SQLModel Task model and Neon PostgreSQL schema with columns and tables for priorities (P1-P4), tags (many-to-many), due dates (timezone-aware), recurrence rules (daily/weekly/monthly/custom cron), and reminders (configurable lead times). Generate Alembic migrations that are safe, reversible, and compatible with existing data.

**Inputs**:
- `feature_name`: Feature being added (e.g., "priorities", "tags", "due_dates", "recurrence", "reminders")
- `model_changes`: Description of new columns, tables, or relationships
- `existing_model_path`: Path to current SQLModel model file (e.g., `backend/models/task.py`)
- `migration_message`: Descriptive Alembic migration message

**Outputs**:
- Updated SQLModel model file with new fields, relationships, and validators
- Alembic migration script (upgrade + downgrade) in `backend/alembic/versions/`
- Pydantic schema updates for API request/response models
- Confirmation that migration is reversible

**Implementation Template**:
```python
# File: backend/models/task.py
# [Skill]: Schema Migration Extensions

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from datetime import datetime, timezone
from enum import Enum
import sqlalchemy as sa

class Priority(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low

class RecurrenceRule(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"  # Uses cron_expression

# Many-to-many link table for tags
class TaskTagLink(SQLModel, table=True):
    __tablename__ = "task_tag_links"
    task_id: str = Field(foreign_key="tasks.id", primary_key=True)
    tag_id: str = Field(foreign_key="tags.id", primary_key=True)

class Tag(SQLModel, table=True):
    __tablename__ = "tags"
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)  # Tags are per-user
    name: str = Field(max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)  # Hex color
    tasks: List["Task"] = Relationship(
        back_populates="tags", link_model=TaskTagLink
    )

    class Config:
        # Unique tag name per user
        table_args = (
            sa.UniqueConstraint("user_id", "name", name="uq_user_tag_name"),
        )

class Task(SQLModel, table=True):
    __tablename__ = "tasks"
    # ... existing fields ...

    # Phase V: Priorities
    priority: Optional[Priority] = Field(default=None, index=True)

    # Phase V: Due Dates (timezone-aware)
    due_at: Optional[datetime] = Field(
        default=None,
        sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True, index=True)
    )

    # Phase V: Recurrence
    recurrence_rule: Optional[RecurrenceRule] = Field(default=None)
    cron_expression: Optional[str] = Field(default=None, max_length=100)
    recurrence_parent_id: Optional[str] = Field(
        default=None, foreign_key="tasks.id"
    )

    # Phase V: Reminders
    remind_before_minutes: Optional[int] = Field(default=None)
    reminder_sent: bool = Field(default=False)

    # Phase V: Tags (many-to-many)
    tags: List[Tag] = Relationship(
        back_populates="tasks", link_model=TaskTagLink
    )
```

```python
# File: backend/alembic/versions/xxxx_add_priorities_tags_recurrence.py
# [Skill]: Schema Migration Extensions — Alembic migration

"""Add priorities, tags, due dates, recurrence, reminders to tasks

Revision ID: xxxx
"""
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # Add priority column to tasks
    op.add_column("tasks", sa.Column(
        "priority", sa.String(2), nullable=True, index=True
    ))
    # Add due_at column
    op.add_column("tasks", sa.Column(
        "due_at", sa.DateTime(timezone=True), nullable=True
    ))
    op.create_index("ix_tasks_due_at", "tasks", ["due_at"])

    # Add recurrence columns
    op.add_column("tasks", sa.Column("recurrence_rule", sa.String(10), nullable=True))
    op.add_column("tasks", sa.Column("cron_expression", sa.String(100), nullable=True))
    op.add_column("tasks", sa.Column(
        "recurrence_parent_id", sa.String, sa.ForeignKey("tasks.id"), nullable=True
    ))

    # Add reminder columns
    op.add_column("tasks", sa.Column("remind_before_minutes", sa.Integer, nullable=True))
    op.add_column("tasks", sa.Column("reminder_sent", sa.Boolean, default=False))

    # Create tags table
    op.create_table(
        "tags",
        sa.Column("id", sa.String, primary_key=True),
        sa.Column("user_id", sa.String, nullable=False, index=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("color", sa.String(7), nullable=True),
        sa.UniqueConstraint("user_id", "name", name="uq_user_tag_name"),
    )

    # Create task-tag link table
    op.create_table(
        "task_tag_links",
        sa.Column("task_id", sa.String, sa.ForeignKey("tasks.id"), primary_key=True),
        sa.Column("tag_id", sa.String, sa.ForeignKey("tags.id"), primary_key=True),
    )

def downgrade() -> None:
    op.drop_table("task_tag_links")
    op.drop_table("tags")
    op.drop_column("tasks", "reminder_sent")
    op.drop_column("tasks", "remind_before_minutes")
    op.drop_column("tasks", "recurrence_parent_id")
    op.drop_column("tasks", "cron_expression")
    op.drop_column("tasks", "recurrence_rule")
    op.drop_index("ix_tasks_due_at", "tasks")
    op.drop_column("tasks", "due_at")
    op.drop_column("tasks", "priority")
```

**Quality Standards**:
- Every migration has both `upgrade()` and `downgrade()` — no one-way migrations
- New columns are `nullable=True` with sensible defaults to avoid breaking existing rows
- Indexes on columns used in WHERE clauses (priority, due_at, user_id)
- Unique constraints enforced at DB level, not just application level
- `alembic upgrade head` and `alembic downgrade -1` both pass without errors
- Existing tests still pass after migration (backward compatible)

---

### 2. Advanced Search, Filter, and Sort

**Purpose**: Implement API endpoints and query builders for searching tasks by keyword, filtering by priority/tags/status/due date range, and sorting by any field. Extends the existing FastAPI tasks router with query parameter composition.

**Inputs**:
- `filter_fields`: List of filterable fields (e.g., priority, status, tag, due_at range)
- `sort_fields`: List of sortable fields (e.g., created_at, due_at, priority, title)
- `search_fields`: Fields to search by keyword (e.g., title, description)
- `existing_router_path`: Path to current tasks API router

**Outputs**:
- Updated FastAPI endpoint with query parameters for search/filter/sort
- SQLModel query builder utility with composable filters
- Pydantic models for filter/sort request validation
- Pagination support (offset/limit with total count)

**Implementation Template**:
```python
# File: backend/api/tasks.py
# [Skill]: Advanced Search, Filter, and Sort

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, col, or_
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/")
async def list_tasks(
    # Auth
    user_id: str = Depends(get_current_user_id),
    # Search
    q: Optional[str] = Query(None, description="Keyword search in title/description"),
    # Filters
    priority: Optional[str] = Query(None, regex="^P[1-4]$"),
    status: Optional[str] = Query(None, regex="^(pending|completed)$"),
    tag: Optional[List[str]] = Query(None, description="Filter by tag names"),
    due_after: Optional[datetime] = Query(None, description="Due date >= this"),
    due_before: Optional[datetime] = Query(None, description="Due date <= this"),
    has_due_date: Optional[bool] = Query(None, description="Filter tasks with/without due dates"),
    # Sort
    sort_by: str = Query("created_at", regex="^(created_at|due_at|priority|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    # Pagination
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    """List tasks with search, filter, sort, and pagination."""
    # Base query — always filter by user_id
    query = select(Task).where(Task.user_id == user_id)

    # Keyword search
    if q:
        search_term = f"%{q}%"
        query = query.where(
            or_(
                col(Task.title).ilike(search_term),
                col(Task.description).ilike(search_term),
            )
        )

    # Priority filter
    if priority:
        query = query.where(Task.priority == priority)

    # Status filter
    if status:
        query = query.where(Task.status == status)

    # Due date range filter
    if due_after:
        query = query.where(Task.due_at >= due_after)
    if due_before:
        query = query.where(Task.due_at <= due_before)
    if has_due_date is not None:
        if has_due_date:
            query = query.where(Task.due_at.isnot(None))
        else:
            query = query.where(Task.due_at.is_(None))

    # Tag filter (requires join)
    if tag:
        query = (
            query
            .join(TaskTagLink, Task.id == TaskTagLink.task_id)
            .join(Tag, TaskTagLink.tag_id == Tag.id)
            .where(Tag.name.in_(tag))
        )

    # Count total before pagination
    count_query = select(sa.func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # Sort
    sort_column = getattr(Task, sort_by)
    if sort_order == "desc":
        query = query.order_by(col(sort_column).desc())
    else:
        query = query.order_by(col(sort_column).asc())

    # Paginate
    query = query.offset(offset).limit(limit)
    tasks = session.exec(query).all()

    return {
        "tasks": [task_to_dict(t) for t in tasks],
        "total": total,
        "offset": offset,
        "limit": limit,
    }
```

**Quality Standards**:
- All queries always include `WHERE user_id = :user_id` — no cross-user leaks
- SQL injection impossible: all filters use SQLModel parameterized queries
- Invalid filter values rejected by Pydantic/Query validators before reaching DB
- Pagination defaults: offset=0, limit=20, max limit=100
- Empty results return `{"tasks": [], "total": 0}` — never 404
- Sort by priority uses defined ordering (P1 > P2 > P3 > P4)
- Performance: indexed columns used in all WHERE/ORDER BY clauses

---

### 3. Kafka Topic Management

**Purpose**: Create, configure, and validate Kafka topics for the event-driven architecture. Covers both self-hosted (Strimzi on Kubernetes) and managed (Redpanda Cloud) deployments. Defines topic schemas, partition strategies, and retention policies.

**Inputs**:
- `deployment_target`: "minikube" (Strimzi/Redpanda Docker) or "cloud" (Redpanda Cloud)
- `topics`: List of topic definitions (name, partitions, retention, schema)
- `kafka_namespace`: Kubernetes namespace for Kafka (default: `kafka`)

**Outputs**:
- Strimzi `KafkaTopic` CRD YAML for self-hosted deployment
- Topic creation commands for Redpanda Cloud
- Event schema definitions (Python dataclasses + JSON Schema)
- Topic verification commands

**Implementation Template**:
```yaml
# File: charts/todo-app/templates/kafka-topics.yaml
# [Skill]: Kafka Topic Management — Strimzi CRD

{{- if .Values.kafka.enabled }}
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-events
  namespace: {{ .Values.kafka.namespace | default "kafka" }}
  labels:
    strimzi.io/cluster: {{ .Values.kafka.clusterName | default "taskflow-kafka" }}
spec:
  partitions: {{ .Values.kafka.topics.taskEvents.partitions | default 3 }}
  replicas: {{ .Values.kafka.topics.taskEvents.replicas | default 1 }}
  config:
    retention.ms: {{ .Values.kafka.topics.taskEvents.retentionMs | default "604800000" }}
    cleanup.policy: "delete"
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: reminders
  namespace: {{ .Values.kafka.namespace | default "kafka" }}
  labels:
    strimzi.io/cluster: {{ .Values.kafka.clusterName | default "taskflow-kafka" }}
spec:
  partitions: {{ .Values.kafka.topics.reminders.partitions | default 1 }}
  replicas: {{ .Values.kafka.topics.reminders.replicas | default 1 }}
  config:
    retention.ms: {{ .Values.kafka.topics.reminders.retentionMs | default "86400000" }}
    cleanup.policy: "delete"
---
apiVersion: kafka.strimzi.io/v1beta2
kind: KafkaTopic
metadata:
  name: task-updates
  namespace: {{ .Values.kafka.namespace | default "kafka" }}
  labels:
    strimzi.io/cluster: {{ .Values.kafka.clusterName | default "taskflow-kafka" }}
spec:
  partitions: {{ .Values.kafka.topics.taskUpdates.partitions | default 3 }}
  replicas: {{ .Values.kafka.topics.taskUpdates.replicas | default 1 }}
  config:
    retention.ms: {{ .Values.kafka.topics.taskUpdates.retentionMs | default "3600000" }}
    cleanup.policy: "delete"
{{- end }}
```

```python
# File: backend/events/schemas.py
# [Skill]: Kafka Topic Management — Event Schemas

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import json
import uuid

@dataclass
class TaskEvent:
    """Schema for task-events topic. Version 1."""
    event_id: str
    event_type: str          # "created" | "updated" | "completed" | "deleted"
    task_id: str
    user_id: str
    task_data: Dict[str, Any]
    timestamp: str           # ISO 8601
    schema_version: int = 1

    @classmethod
    def create(cls, event_type: str, task_id: str, user_id: str, task_data: dict):
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            task_id=task_id,
            user_id=user_id,
            task_data=task_data,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

@dataclass
class ReminderEvent:
    """Schema for reminders topic. Version 1."""
    event_id: str
    task_id: str
    user_id: str
    title: str
    due_at: str              # ISO 8601
    remind_at: str           # ISO 8601
    schema_version: int = 1

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")

@dataclass
class TaskUpdateEvent:
    """Schema for task-updates topic (real-time sync). Version 1."""
    event_id: str
    event_type: str          # "created" | "updated" | "completed" | "deleted"
    task_id: str
    user_id: str
    changes: Dict[str, Any]  # Only changed fields
    timestamp: str
    schema_version: int = 1

    def to_json(self) -> bytes:
        return json.dumps(asdict(self)).encode("utf-8")
```

**Quality Standards**:
- All event schemas include `schema_version` for future evolution
- Every event has a unique `event_id` (UUID4) for idempotency tracking
- Timestamps are ISO 8601 in UTC — no ambiguous formats
- Topic partitions keyed by `user_id` for ordering guarantees per user
- Retention policies: `task-events` 7 days, `reminders` 1 day, `task-updates` 1 hour
- Strimzi CRD YAML validates with `kubectl apply --dry-run=client`
- Minikube: single replica per topic; cloud: 3 replicas for fault tolerance

---

### 4. Kafka Producer-Consumer

**Purpose**: Implement Kafka producers (in Chat API / MCP Tools) and consumers (Notification Service, Recurring Task Service, Audit Service, WebSocket Service) using `aiokafka` for async Python. Ensures at-least-once delivery, idempotent consumers, and dead-letter queue handling.

**Inputs**:
- `role`: "producer" or "consumer"
- `topic`: Kafka topic name
- `event_schema`: Event dataclass reference
- `consumer_group`: Consumer group ID (for consumers)
- `connection_config`: Bootstrap servers, SASL credentials (from env/Dapr secrets)

**Outputs**:
- Producer class with `publish()` method and error handling
- Consumer class with message processing loop and graceful shutdown
- Dead-letter queue handler for failed messages
- Health check endpoint for consumer readiness

**Implementation Template**:
```python
# File: backend/events/producer.py
# [Skill]: Kafka Producer-Consumer — Producer

import logging
from aiokafka import AIOKafkaProducer
from backend.events.schemas import TaskEvent, ReminderEvent
from backend.core.config import settings

logger = logging.getLogger(__name__)

class EventProducer:
    """Async Kafka producer for task events."""

    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
            value_serializer=lambda v: v,  # Events pre-serialized
            acks="all",                     # Wait for all replicas
            retries=3,
            retry_backoff_ms=500,
        )
        await self._producer.start()
        logger.info("Kafka producer started")

    async def stop(self):
        if self._producer:
            await self._producer.stop()
            logger.info("Kafka producer stopped")

    async def publish_task_event(
        self, event_type: str, task_id: str, user_id: str, task_data: dict
    ):
        """Publish a task event to the task-events topic."""
        event = TaskEvent.create(event_type, task_id, user_id, task_data)
        await self._producer.send_and_wait(
            topic="task-events",
            value=event.to_json(),
            key=user_id.encode("utf-8"),  # Partition by user
        )
        logger.info(f"Published {event_type} event for task {task_id}")

    async def publish_reminder(self, reminder: ReminderEvent):
        """Publish a reminder event to the reminders topic."""
        await self._producer.send_and_wait(
            topic="reminders",
            value=reminder.to_json(),
            key=reminder.user_id.encode("utf-8"),
        )
        logger.info(f"Published reminder for task {reminder.task_id}")

# Singleton instance — initialized on app startup
event_producer = EventProducer()
```

```python
# File: backend/events/consumer.py
# [Skill]: Kafka Producer-Consumer — Consumer base class

import logging
import asyncio
from aiokafka import AIOKafkaConsumer
from abc import ABC, abstractmethod
from typing import Set
from backend.core.config import settings

logger = logging.getLogger(__name__)

class BaseConsumer(ABC):
    """Base class for Kafka consumers with at-least-once delivery."""

    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self._consumer: AIOKafkaConsumer | None = None
        self._running = False
        self._processed_ids: Set[str] = set()  # Idempotency window

    async def start(self):
        self._consumer = AIOKafkaConsumer(
            self.topic,
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            group_id=self.group_id,
            security_protocol=settings.KAFKA_SECURITY_PROTOCOL,
            sasl_mechanism=settings.KAFKA_SASL_MECHANISM,
            sasl_plain_username=settings.KAFKA_USERNAME,
            sasl_plain_password=settings.KAFKA_PASSWORD,
            auto_offset_reset="earliest",
            enable_auto_commit=False,      # Manual commit after processing
            max_poll_records=10,
        )
        await self._consumer.start()
        self._running = True
        logger.info(f"Consumer [{self.group_id}] started on topic [{self.topic}]")

    async def stop(self):
        self._running = False
        if self._consumer:
            await self._consumer.stop()
        logger.info(f"Consumer [{self.group_id}] stopped")

    async def run(self):
        """Main consumption loop."""
        await self.start()
        try:
            async for msg in self._consumer:
                try:
                    event = self.deserialize(msg.value)
                    event_id = event.get("event_id", "")

                    # Idempotency check
                    if event_id in self._processed_ids:
                        logger.debug(f"Skipping duplicate event {event_id}")
                        await self._consumer.commit()
                        continue

                    await self.handle(event)
                    self._processed_ids.add(event_id)

                    # Trim idempotency window
                    if len(self._processed_ids) > 10000:
                        self._processed_ids = set(
                            list(self._processed_ids)[-5000:]
                        )

                    await self._consumer.commit()

                except Exception as e:
                    logger.error(f"Error processing message: {e}")
                    await self.handle_dead_letter(msg, e)
                    await self._consumer.commit()

                if not self._running:
                    break
        finally:
            await self.stop()

    @abstractmethod
    async def handle(self, event: dict):
        """Process a single event. Override in subclasses."""
        ...

    def deserialize(self, value: bytes) -> dict:
        import json
        return json.loads(value.decode("utf-8"))

    async def handle_dead_letter(self, msg, error):
        """Send failed messages to dead-letter topic."""
        logger.error(
            f"Dead letter: topic={self.topic} offset={msg.offset} error={error}"
        )
        # In production: publish to {topic}-dlq
```

```python
# File: backend/services/recurring_task_consumer.py
# [Skill]: Kafka Producer-Consumer — Recurring Task Service

from backend.events.consumer import BaseConsumer
from sqlmodel import Session
from backend.database import engine
from backend.models.task import Task
import logging

logger = logging.getLogger(__name__)

class RecurringTaskConsumer(BaseConsumer):
    """Consumes task-events and creates next occurrence of recurring tasks."""

    def __init__(self):
        super().__init__(topic="task-events", group_id="recurring-task-service")

    async def handle(self, event: dict):
        if event["event_type"] != "completed":
            return

        task_data = event["task_data"]
        if not task_data.get("recurrence_rule"):
            return

        # Create next occurrence
        with Session(engine) as session:
            original = session.get(Task, event["task_id"])
            if not original or not original.recurrence_rule:
                return

            next_due = calculate_next_due(
                original.due_at, original.recurrence_rule, original.cron_expression
            )

            new_task = Task(
                user_id=event["user_id"],
                title=original.title,
                description=original.description,
                priority=original.priority,
                due_at=next_due,
                recurrence_rule=original.recurrence_rule,
                cron_expression=original.cron_expression,
                recurrence_parent_id=original.id,
                status="pending",
            )
            session.add(new_task)
            session.commit()
            logger.info(
                f"Created next recurring task for user {event['user_id']}, "
                f"due {next_due}"
            )
```

**Quality Standards**:
- Producers use `acks="all"` for durable writes; `send_and_wait()` confirms delivery
- Consumers use manual commit (`enable_auto_commit=False`) — commit only after successful processing
- Every consumer implements idempotency via `event_id` tracking
- Dead-letter queue handler logs and optionally republishes to `{topic}-dlq`
- Graceful shutdown: `stop()` called on SIGTERM, in-flight messages complete first
- Connection credentials loaded from environment variables, never hardcoded
- Health check returns unhealthy if consumer loop is not running
- Consumer group IDs are unique per service (e.g., `recurring-task-service`, `notification-service`)

---

### 5. Dapr Component Setup

**Purpose**: Define and configure Dapr component YAML files for all five building blocks used in the Todo Chatbot: Pub/Sub (Kafka), State Management (Redis/PostgreSQL), Service Invocation, Bindings (cron for reminders), and Secrets Management. Components are swappable without code changes.

**Inputs**:
- `building_block`: One of "pubsub", "state", "bindings", "secrets", "service-invocation"
- `backend_type`: Implementation backend (e.g., "kafka", "redis", "postgres", "kubernetes")
- `deployment_target`: "minikube" or "cloud" (affects connection details)
- `component_name`: Dapr component name (e.g., "taskflow-pubsub")

**Outputs**:
- Dapr component YAML file in `charts/todo-app/templates/dapr/`
- Helm values entries for component configuration
- Python code for interacting with Dapr HTTP API
- Verification commands for component health

**Implementation Template**:
```yaml
# File: charts/todo-app/templates/dapr/pubsub-kafka.yaml
# [Skill]: Dapr Component Setup — Pub/Sub (Kafka)

apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-pubsub
  namespace: {{ .Values.global.namespace }}
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: {{ .Values.dapr.pubsub.brokers }}
    - name: authType
      value: {{ .Values.dapr.pubsub.authType | default "none" }}
    {{- if eq .Values.dapr.pubsub.authType "password" }}
    - name: saslUsername
      secretKeyRef:
        name: kafka-credentials
        key: username
    - name: saslPassword
      secretKeyRef:
        name: kafka-credentials
        key: password
    {{- end }}
    - name: consumerGroup
      value: "{{ .Release.Name }}-consumer"
    - name: maxMessageBytes
      value: "1048576"
```

```yaml
# File: charts/todo-app/templates/dapr/statestore.yaml
# [Skill]: Dapr Component Setup — State Management

apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-statestore
  namespace: {{ .Values.global.namespace }}
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: {{ .Values.global.secretName }}
        key: database-url
    - name: tableName
      value: "dapr_state"
    - name: keyPrefix
      value: "name"
```

```yaml
# File: charts/todo-app/templates/dapr/binding-cron.yaml
# [Skill]: Dapr Component Setup — Cron Binding for Reminders

apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-cron
  namespace: {{ .Values.global.namespace }}
spec:
  type: bindings.cron
  version: v1
  metadata:
    - name: schedule
      value: {{ .Values.dapr.bindings.reminderCron | default "@every 1m" }}
    - name: direction
      value: "input"
```

```yaml
# File: charts/todo-app/templates/dapr/secretstore.yaml
# [Skill]: Dapr Component Setup — Secrets Management

apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-secrets
  namespace: {{ .Values.global.namespace }}
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

```python
# File: backend/dapr/client.py
# [Skill]: Dapr Component Setup — Python HTTP Client

import httpx
import logging
from backend.core.config import settings

logger = logging.getLogger(__name__)

DAPR_HTTP_PORT = settings.DAPR_HTTP_PORT or "3500"
DAPR_BASE_URL = f"http://localhost:{DAPR_HTTP_PORT}/v1.0"

async def dapr_publish(pubsub_name: str, topic: str, data: dict):
    """Publish event via Dapr Pub/Sub API."""
    url = f"{DAPR_BASE_URL}/publish/{pubsub_name}/{topic}"
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=data)
        resp.raise_for_status()
    logger.info(f"Published to {pubsub_name}/{topic}")

async def dapr_get_state(store_name: str, key: str) -> dict | None:
    """Get state via Dapr State API."""
    url = f"{DAPR_BASE_URL}/state/{store_name}/{key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        if resp.status_code == 204:
            return None
        resp.raise_for_status()
        return resp.json()

async def dapr_save_state(store_name: str, key: str, value: dict):
    """Save state via Dapr State API."""
    url = f"{DAPR_BASE_URL}/state/{store_name}"
    payload = [{"key": key, "value": value}]
    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()

async def dapr_invoke_service(app_id: str, method: str, data: dict = None) -> dict:
    """Invoke another service via Dapr Service Invocation API."""
    url = f"{DAPR_BASE_URL}/invoke/{app_id}/method/{method}"
    async with httpx.AsyncClient() as client:
        if data:
            resp = await client.post(url, json=data)
        else:
            resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()

async def dapr_get_secret(store_name: str, secret_name: str) -> dict:
    """Get secret via Dapr Secrets API."""
    url = f"{DAPR_BASE_URL}/secrets/{store_name}/{secret_name}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        return resp.json()
```

**Quality Standards**:
- Application code ONLY talks to Dapr HTTP APIs (`localhost:3500`) — never directly to Kafka/Redis
- All component YAMLs pass `kubectl apply --dry-run=client` validation
- Secrets referenced via `secretKeyRef` — never inline in component YAML
- Components are swappable: changing `pubsub.kafka` to `pubsub.redis` requires only YAML change, zero code changes
- Dapr sidecar health checked via `GET /v1.0/healthz` before accepting traffic
- Helm values provide per-environment overrides (minikube vs cloud)
- Error handling: `httpx.HTTPStatusError` caught and logged in all Dapr client methods

---

### 6. Event-Driven Service Creation

**Purpose**: Create standalone microservices that consume Kafka events via Dapr Pub/Sub: Notification Service (sends reminders), Recurring Task Service (creates next occurrences), Audit Service (stores activity log), and WebSocket Service (broadcasts real-time updates). Each service runs as a separate Kubernetes deployment with its own Dapr sidecar.

**Inputs**:
- `service_name`: Name of the service (e.g., "notification-service")
- `consumed_topics`: Topics this service subscribes to
- `event_handler`: Business logic for processing events
- `dapr_app_id`: Dapr application ID for this service

**Outputs**:
- FastAPI service with Dapr subscription endpoint
- Dockerfile for the service
- Helm deployment template with Dapr sidecar annotations
- Health check and readiness endpoints

**Implementation Template**:
```python
# File: services/notification/main.py
# [Skill]: Event-Driven Service Creation — Notification Service

from fastapi import FastAPI, Request
import logging
from datetime import datetime, timezone

app = FastAPI(title="Notification Service")
logger = logging.getLogger(__name__)

# Dapr subscription declaration
@app.get("/dapr/subscribe")
async def subscribe():
    """Tell Dapr which topics this service subscribes to."""
    return [
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "reminders",
            "route": "/events/reminders",
        },
    ]

@app.post("/events/reminders")
async def handle_reminder(request: Request):
    """Process reminder events from Kafka via Dapr Pub/Sub."""
    event = await request.json()
    data = event.get("data", {})

    task_id = data.get("task_id")
    user_id = data.get("user_id")
    title = data.get("title")
    remind_at = data.get("remind_at")

    logger.info(f"Reminder for user {user_id}: task '{title}' due soon")

    # Check if reminder time has arrived
    remind_time = datetime.fromisoformat(remind_at)
    if datetime.now(timezone.utc) >= remind_time:
        await send_notification(user_id, title, data.get("due_at"))

    return {"status": "SUCCESS"}  # Dapr expects SUCCESS to ack

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}

async def send_notification(user_id: str, title: str, due_at: str):
    """Send notification to user. Extensible to push/email/SMS."""
    logger.info(f"NOTIFY user={user_id}: Task '{title}' due at {due_at}")
    # Integration point: push notification, email, or WebSocket
```

```python
# File: services/audit/main.py
# [Skill]: Event-Driven Service Creation — Audit Service

from fastapi import FastAPI, Request
from sqlmodel import Session, SQLModel, Field, create_engine
from datetime import datetime
import logging
import os

app = FastAPI(title="Audit Service")
logger = logging.getLogger(__name__)

engine = create_engine(os.environ["DATABASE_URL"])

class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    id: int | None = Field(default=None, primary_key=True)
    event_type: str
    task_id: str
    user_id: str
    event_data: str  # JSON string
    timestamp: datetime

@app.get("/dapr/subscribe")
async def subscribe():
    return [
        {
            "pubsubname": "taskflow-pubsub",
            "topic": "task-events",
            "route": "/events/task-events",
        },
    ]

@app.post("/events/task-events")
async def handle_task_event(request: Request):
    """Store every task operation in the audit log."""
    event = await request.json()
    data = event.get("data", {})

    with Session(engine) as session:
        log = AuditLog(
            event_type=data.get("event_type", "unknown"),
            task_id=data.get("task_id", ""),
            user_id=data.get("user_id", ""),
            event_data=str(data),
            timestamp=datetime.fromisoformat(
                data.get("timestamp", datetime.utcnow().isoformat())
            ),
        )
        session.add(log)
        session.commit()

    logger.info(f"Audit: {data.get('event_type')} task {data.get('task_id')}")
    return {"status": "SUCCESS"}

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "audit-service"}
```

**Quality Standards**:
- Every service exposes `GET /dapr/subscribe` for Dapr topic subscription discovery
- Event handlers return `{"status": "SUCCESS"}` to Dapr for message acknowledgment
- Failed processing returns `{"status": "RETRY"}` or `{"status": "DROP"}` per Dapr spec
- Each service has its own `Dockerfile`, `requirements.txt`, and Helm deployment template
- Health endpoints at `GET /health` for Kubernetes probes
- Services are stateless — all persistent state goes through Dapr state store or database
- Dapr app-id annotations on deployments match the subscription configuration
- Logging includes correlation IDs (event_id) for distributed tracing

---

### 7. Domain Event Emission

**Purpose**: Integrate event publishing hooks into existing CRUD operations in the Chat API and MCP Tools. Every task create/update/complete/delete emits a `TaskEvent` to Kafka (via Dapr Pub/Sub or direct aiokafka). Reminder events are emitted when due dates are set.

**Inputs**:
- `operation`: CRUD operation being instrumented (create, update, complete, delete)
- `existing_code_path`: Path to the CRUD function or MCP tool being extended
- `event_schema`: Event dataclass to use (TaskEvent, ReminderEvent)
- `publish_method`: "dapr" (HTTP API) or "direct" (aiokafka producer)

**Outputs**:
- Modified CRUD function with event emission after successful DB commit
- Helper function for constructing events from task objects
- Configuration for choosing Dapr vs direct Kafka

**Implementation Template**:
```python
# File: backend/events/emit.py
# [Skill]: Domain Event Emission — Unified emitter

import logging
from backend.events.schemas import TaskEvent, ReminderEvent
from backend.core.config import settings

logger = logging.getLogger(__name__)

async def emit_task_event(
    event_type: str,
    task_id: str,
    user_id: str,
    task_data: dict,
):
    """Emit a task event via configured transport (Dapr or direct Kafka)."""
    event = TaskEvent.create(event_type, task_id, user_id, task_data)

    if settings.USE_DAPR:
        from backend.dapr.client import dapr_publish
        await dapr_publish(
            pubsub_name="taskflow-pubsub",
            topic="task-events",
            data=event.__dict__,
        )
    else:
        from backend.events.producer import event_producer
        await event_producer.publish_task_event(
            event_type, task_id, user_id, task_data
        )

    logger.info(f"Emitted {event_type} event for task {task_id}")

async def emit_reminder_if_needed(task, user_id: str):
    """Emit a reminder event if task has a due date and reminder configured."""
    if not task.due_at or not task.remind_before_minutes:
        return

    from datetime import timedelta
    remind_at = task.due_at - timedelta(minutes=task.remind_before_minutes)

    reminder = ReminderEvent(
        event_id=str(__import__("uuid").uuid4()),
        task_id=str(task.id),
        user_id=user_id,
        title=task.title,
        due_at=task.due_at.isoformat(),
        remind_at=remind_at.isoformat(),
    )

    if settings.USE_DAPR:
        from backend.dapr.client import dapr_publish
        await dapr_publish(
            pubsub_name="taskflow-pubsub",
            topic="reminders",
            data=reminder.__dict__,
        )
    else:
        from backend.events.producer import event_producer
        await event_producer.publish_reminder(reminder)

    logger.info(f"Emitted reminder for task {task.id}, remind at {remind_at}")
```

```python
# File: mcp/tools/add_task.py (modified)
# [Skill]: Domain Event Emission — Instrumented MCP Tool

from sqlmodel import Session
from app.models import Task
from app.database import engine
from backend.events.emit import emit_task_event, emit_reminder_if_needed
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

async def add_task(user_id: str, title: str, description: Optional[str] = None,
                   priority: Optional[str] = None, due_at: Optional[str] = None,
                   remind_before_minutes: Optional[int] = None) -> Dict:
    """Create a new task and emit domain events."""
    with Session(engine) as session:
        new_task = Task(
            user_id=user_id,
            title=title.strip(),
            description=description,
            priority=priority,
            due_at=due_at,
            remind_before_minutes=remind_before_minutes,
        )
        session.add(new_task)
        session.commit()
        session.refresh(new_task)

    # Emit events AFTER successful commit
    task_dict = {
        "id": new_task.id, "title": new_task.title,
        "status": new_task.status, "priority": new_task.priority,
    }
    await emit_task_event("created", str(new_task.id), user_id, task_dict)
    await emit_reminder_if_needed(new_task, user_id)

    return {"task_id": new_task.id, "status": "created", "title": new_task.title}
```

**Quality Standards**:
- Events emitted AFTER successful database commit — never before (avoids phantom events)
- Event emission failures are logged but do NOT fail the CRUD operation (fire-and-forget with retry)
- `USE_DAPR` config toggle switches between Dapr HTTP and direct aiokafka — same event schemas either way
- Every modified CRUD function has its event emission tested (mock producer in tests)
- Reminder events only emitted when both `due_at` AND `remind_before_minutes` are set
- Task data in events is minimal (ID, title, status, changed fields) — not the full DB row

---

### 8. Helm Dapr Sidecar Injection

**Purpose**: Update Phase IV Helm chart templates to enable Dapr sidecar injection on all application deployments. Add Dapr annotations, configure sidecar ports, and include Dapr component definitions in the chart. Supports toggling Dapr on/off via Helm values.

**Inputs**:
- `deployment_template_path`: Path to existing Helm deployment template
- `dapr_app_id`: Dapr application ID for the service
- `dapr_app_port`: Port the application listens on
- `dapr_enabled`: Whether to enable Dapr for this deployment (toggleable)

**Outputs**:
- Modified deployment template with Dapr sidecar annotations
- Updated `values.yaml` with Dapr configuration section
- Dapr component YAML templates included in chart
- Verification commands for sidecar injection

**Implementation Template**:
```yaml
# File: charts/todo-app/templates/backend-deployment.yaml (modified)
# [Skill]: Helm Dapr Sidecar Injection

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "todo-chatbot.fullname" . }}-backend
  namespace: {{ .Values.global.namespace }}
  labels:
    {{- include "todo-chatbot.labels" . | nindent 4 }}
    app.kubernetes.io/component: backend
spec:
  replicas: {{ .Values.backend.replicaCount }}
  selector:
    matchLabels:
      {{- include "todo-chatbot.selectorLabels" . | nindent 6 }}
      app.kubernetes.io/component: backend
  template:
    metadata:
      labels:
        {{- include "todo-chatbot.selectorLabels" . | nindent 8 }}
        app.kubernetes.io/component: backend
      annotations:
        {{- if .Values.dapr.enabled }}
        dapr.io/enabled: "true"
        dapr.io/app-id: "{{ .Values.backend.dapr.appId | default "todo-backend" }}"
        dapr.io/app-port: "{{ .Values.backend.service.port }}"
        dapr.io/app-protocol: "http"
        dapr.io/log-level: "{{ .Values.dapr.logLevel | default "info" }}"
        dapr.io/enable-metrics: "true"
        dapr.io/metrics-port: "9090"
        dapr.io/sidecar-cpu-request: "100m"
        dapr.io/sidecar-memory-request: "64Mi"
        dapr.io/sidecar-cpu-limit: "300m"
        dapr.io/sidecar-memory-limit: "128Mi"
        {{- end }}
    spec:
      containers:
        - name: backend
          image: "{{ .Values.backend.image.repository }}:{{ .Values.backend.image.tag }}"
          # ... rest of container spec unchanged ...
          env:
            - name: DAPR_HTTP_PORT
              value: "3500"
            - name: USE_DAPR
              value: "{{ .Values.dapr.enabled }}"
```

```yaml
# File: charts/todo-app/values.yaml (Dapr section addition)
# [Skill]: Helm Dapr Sidecar Injection

# -- Dapr Configuration
dapr:
  enabled: false                # Toggle Dapr on/off globally
  logLevel: info                # debug | info | warn | error
  pubsub:
    brokers: "taskflow-kafka-kafka-bootstrap.kafka.svc:9092"
    authType: none              # none (minikube) | password (cloud)
  stateStore:
    type: postgresql
  bindings:
    reminderCron: "@every 1m"
  # Per-service Dapr app IDs
  backend:
    appId: todo-backend
  notificationService:
    appId: notification-service
  recurringTaskService:
    appId: recurring-task-service
  auditService:
    appId: audit-service
```

**Quality Standards**:
- Dapr annotations are conditional: `{{- if .Values.dapr.enabled }}` — chart works without Dapr
- Sidecar resource limits set (100m/64Mi request, 300m/128Mi limit) to avoid Minikube OOM
- `dapr.io/app-port` matches the container's actual listening port
- `dapr.io/app-id` is unique per deployment — collisions cause routing errors
- After `helm upgrade`: verify sidecars with `kubectl get pods -n todo-app -o jsonpath='{.items[*].spec.containers[*].name}'`
- Dapr health checked: `kubectl exec <pod> -c daprd -- wget -qO- http://localhost:3500/v1.0/healthz`
- All Dapr component YAMLs included in `templates/dapr/` subdirectory

---

### 9. Cloud Cluster Provisioning

**Purpose**: Provision production-grade Kubernetes clusters on Oracle OKE (primary, always-free), Azure AKS, or Google Cloud GKE. Configure kubectl access, install Dapr, and prepare the cluster for Helm-based deployment. Includes cost-awareness and resource optimization.

**Inputs**:
- `cloud_provider`: "oke" | "aks" | "gke"
- `cluster_name`: Name for the Kubernetes cluster
- `node_config`: Node pool configuration (size, count, machine type)
- `region`: Cloud region for deployment

**Outputs**:
- Cloud CLI commands for cluster creation
- kubectl configuration for cluster access
- Dapr installation commands for the cloud cluster
- Ingress controller setup (NGINX or cloud-native)
- Cost estimation and resource limits

**Implementation Template**:
```bash
# [Skill]: Cloud Cluster Provisioning — Oracle OKE (Recommended)
# Always-free tier: 4 OCPUs, 24GB RAM, no charge after trial

# Prerequisites
oci setup config  # One-time OCI CLI configuration

# Create OKE cluster
oci ce cluster create \
  --compartment-id $COMPARTMENT_ID \
  --name todo-chatbot-cluster \
  --kubernetes-version v1.28.0 \
  --vcn-id $VCN_ID \
  --service-lb-subnet-ids '["'$LB_SUBNET_ID'"]' \
  --endpoint-subnet-id $ENDPOINT_SUBNET_ID

# Create node pool (always-free ARM shapes)
oci ce node-pool create \
  --compartment-id $COMPARTMENT_ID \
  --cluster-id $CLUSTER_ID \
  --name todo-node-pool \
  --kubernetes-version v1.28.0 \
  --node-shape VM.Standard.A1.Flex \
  --node-shape-config '{"ocpus": 2, "memoryInGBs": 12}' \
  --size 2 \
  --placement-configs '[{"availabilityDomain": "'$AD'", "subnetId": "'$NODE_SUBNET_ID'"}]'

# Configure kubectl
oci ce cluster create-kubeconfig \
  --cluster-id $CLUSTER_ID \
  --file ~/.kube/config \
  --region $REGION \
  --token-version 2.0.0

kubectl get nodes  # Verify access
```

```bash
# [Skill]: Cloud Cluster Provisioning — Azure AKS
# $200 credit for 30 days

az login
az group create --name todo-chatbot-rg --location eastus

az aks create \
  --resource-group todo-chatbot-rg \
  --name todo-chatbot-aks \
  --node-count 2 \
  --node-vm-size Standard_B2s \
  --generate-ssh-keys \
  --enable-managed-identity

az aks get-credentials \
  --resource-group todo-chatbot-rg \
  --name todo-chatbot-aks
```

```bash
# [Skill]: Cloud Cluster Provisioning — Google Cloud GKE
# $300 credit for 90 days

gcloud auth login
gcloud config set project $PROJECT_ID

gcloud container clusters create todo-chatbot-gke \
  --zone us-central1-a \
  --num-nodes 2 \
  --machine-type e2-medium \
  --disk-size 30 \
  --enable-ip-alias

gcloud container clusters get-credentials todo-chatbot-gke \
  --zone us-central1-a
```

```bash
# [Skill]: Cloud Cluster Provisioning — Common post-setup (all providers)

# Install Dapr on the cluster
dapr init -k --runtime-version 1.13.0

# Verify Dapr installation
dapr status -k
kubectl get pods -n dapr-system

# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer

# Create application namespace
kubectl create namespace todo-app
```

**Quality Standards**:
- Oracle OKE preferred: always-free tier (4 OCPUs, 24GB RAM) — no credit card charge after trial
- AKS/GKE use smallest viable node sizes (Standard_B2s / e2-medium) to conserve credits
- `kubectl get nodes` verification after every cluster creation
- Dapr installed with specific version pin (`--runtime-version`) for reproducibility
- NGINX Ingress Controller deployed for external access
- All credentials managed via cloud CLI auth — never stored in files committed to git
- Cluster creation commands include `--dry-run` or equivalent for preview

---

### 10. GitHub Actions CI/CD

**Purpose**: Configure multi-stage GitHub Actions workflows for automated lint, test, build, push, and deploy of the Todo Chatbot to cloud Kubernetes. Includes Docker image caching, Helm-based deployment, environment-specific configs, and one-click rollback.

**Inputs**:
- `target_cloud`: "oke" | "aks" | "gke"
- `registry`: Container registry (GHCR, Docker Hub, or cloud-native)
- `helm_chart_path`: Path to Helm chart in repository
- `environments`: List of deployment environments (e.g., staging, production)

**Outputs**:
- `.github/workflows/ci-cd.yml` workflow file
- Dockerfile for each service (if not existing)
- Helm values overrides per environment
- Rollback workflow or commands

**Implementation Template**:
```yaml
# File: .github/workflows/ci-cd.yml
# [Skill]: GitHub Actions CI/CD

name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_PREFIX: ${{ github.repository_owner }}/todo-chatbot

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Lint (ruff)
        run: |
          cd backend
          ruff check .
          ruff format --check .

      - name: Test
        run: |
          cd backend
          pytest --cov=. --cov-report=xml -q
        env:
          DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
          BETTER_AUTH_SECRET: test-secret

      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  build-and-push:
    needs: lint-and-test
    runs-on: ubuntu-latest
    if: github.event_name == 'push'
    strategy:
      matrix:
        service: [backend, frontend, notification-service, recurring-task-service]
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4

      - name: Log in to GHCR
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: |
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:${{ github.sha }}
            ${{ env.REGISTRY }}/${{ env.IMAGE_PREFIX }}-${{ matrix.service }}:latest
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - uses: actions/checkout@v4

      - name: Install Helm
        uses: azure/setup-helm@v3

      - name: Configure kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBECONFIG }}

      - name: Deploy with Helm
        run: |
          helm upgrade --install todo-chatbot ./charts/todo-app \
            --namespace todo-app \
            --create-namespace \
            --set backend.image.tag=${{ github.sha }} \
            --set frontend.image.tag=${{ github.sha }} \
            --set backend.env.DATABASE_URL=${{ secrets.DATABASE_URL }} \
            --set backend.env.BETTER_AUTH_SECRET=${{ secrets.BETTER_AUTH_SECRET }} \
            --set backend.env.OPENAI_API_KEY=${{ secrets.OPENAI_API_KEY }} \
            --set dapr.enabled=true \
            --set dapr.pubsub.brokers=${{ secrets.KAFKA_BROKERS }} \
            --atomic \
            --timeout 10m \
            --wait

      - name: Verify deployment
        run: |
          kubectl rollout status deployment/todo-chatbot-backend -n todo-app --timeout=300s
          kubectl rollout status deployment/todo-chatbot-frontend -n todo-app --timeout=300s

      - name: Smoke test
        run: |
          BACKEND_URL=$(kubectl get svc todo-chatbot-backend -n todo-app -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
          curl -sf "http://${BACKEND_URL}:8000/health" || exit 1
```

```yaml
# File: .github/workflows/rollback.yml
# [Skill]: GitHub Actions CI/CD — Rollback workflow

name: Rollback Deployment

on:
  workflow_dispatch:
    inputs:
      revision:
        description: 'Helm revision to rollback to (0 = previous)'
        required: false
        default: '0'

jobs:
  rollback:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - name: Configure kubectl
        uses: azure/k8s-set-context@v4
        with:
          kubeconfig: ${{ secrets.KUBECONFIG }}

      - name: Install Helm
        uses: azure/setup-helm@v3

      - name: Rollback
        run: |
          helm rollback todo-chatbot ${{ github.event.inputs.revision }} \
            --namespace todo-app \
            --wait --timeout 5m

      - name: Verify rollback
        run: |
          kubectl rollout status deployment/todo-chatbot-backend -n todo-app
          kubectl get pods -n todo-app
```

**Quality Standards**:
- Pipeline runs in under 15 minutes total (lint+test+build+deploy)
- Docker images tagged with git SHA for traceability — `latest` tag for convenience
- Build caching via GitHub Actions cache (`type=gha`) — rebuilds only changed layers
- `--atomic` flag on Helm upgrade: auto-rollback on deployment failure
- Zero-downtime: rolling update strategy with readiness probes
- Rollback is one-click via `workflow_dispatch` or `helm rollback` command
- Secrets managed via GitHub Secrets — never in workflow files or Helm values committed to repo
- Branch protection: `main` requires passing CI before merge

---

### 11. Observability Stack Setup

**Purpose**: Deploy monitoring (Prometheus + Grafana), logging (Loki), and distributed tracing (Jaeger via Dapr) to the Kubernetes cluster. Provision dashboards as code and configure alerting rules for critical conditions.

**Inputs**:
- `deployment_target`: "minikube" or "cloud"
- `services_to_monitor`: List of services (backend, frontend, notification, recurring-task)
- `alert_thresholds`: Configurable thresholds for alerts
- `dashboard_definitions`: Grafana dashboard JSON definitions

**Outputs**:
- Helm values for kube-prometheus-stack
- Grafana dashboard ConfigMaps (provisioned as code)
- Prometheus alert rules YAML
- Loki + Promtail configuration
- Jaeger setup via Dapr tracing configuration
- Verification commands

**Implementation Template**:
```bash
# [Skill]: Observability Stack Setup — Installation commands

# Add Helm repos
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

# Install Prometheus + Grafana (kube-prometheus-stack)
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  --set prometheus.prometheusSpec.resources.requests.memory=256Mi \
  --set prometheus.prometheusSpec.resources.limits.memory=512Mi \
  --set grafana.resources.requests.memory=128Mi \
  --set grafana.resources.limits.memory=256Mi \
  --set grafana.adminPassword="${GRAFANA_ADMIN_PASSWORD}" \
  --values charts/monitoring/prometheus-values.yaml

# Install Loki for log aggregation
helm install loki grafana/loki-stack \
  --namespace monitoring \
  --set loki.resources.requests.memory=128Mi \
  --set loki.resources.limits.memory=256Mi \
  --set promtail.enabled=true

# Access Grafana
kubectl port-forward svc/monitoring-grafana -n monitoring 3001:80
# Default: admin / ${GRAFANA_ADMIN_PASSWORD}
```

```yaml
# File: charts/monitoring/prometheus-values.yaml
# [Skill]: Observability Stack Setup — Prometheus config

prometheus:
  prometheusSpec:
    serviceMonitorSelectorNilUsesHelmValues: false
    podMonitorSelectorNilUsesHelmValues: false
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        cpu: 500m
        memory: 512Mi

grafana:
  dashboardProviders:
    dashboardproviders.yaml:
      apiVersion: 1
      providers:
        - name: 'todo-chatbot'
          orgId: 1
          folder: 'Todo Chatbot'
          type: file
          options:
            path: /var/lib/grafana/dashboards/todo-chatbot

  dashboardsConfigMaps:
    todo-chatbot: "grafana-dashboards-todo"

alertmanager:
  config:
    route:
      group_by: ['alertname', 'namespace']
      group_wait: 10s
      group_interval: 5m
      repeat_interval: 3h
```

```yaml
# File: charts/monitoring/alert-rules.yaml
# [Skill]: Observability Stack Setup — Alert Rules

apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: todo-chatbot-alerts
  namespace: monitoring
spec:
  groups:
    - name: todo-chatbot.rules
      rules:
        - alert: PodRestartsTooHigh
          expr: increase(kube_pod_container_status_restarts_total{namespace="todo-app"}[5m]) > 3
          for: 2m
          labels:
            severity: warning
          annotations:
            summary: "Pod {{ $labels.pod }} restarting too frequently"

        - alert: HighErrorRate
          expr: |
            sum(rate(http_requests_total{namespace="todo-app", status=~"5.."}[5m]))
            / sum(rate(http_requests_total{namespace="todo-app"}[5m])) > 0.05
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: "Error rate above 5% in todo-app"

        - alert: HighP95Latency
          expr: |
            histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{namespace="todo-app"}[5m])) by (le, service)) > 2
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "P95 latency above 2s for {{ $labels.service }}"

        - alert: KafkaConsumerLagHigh
          expr: kafka_consumer_group_lag{namespace="todo-app"} > 1000
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: "Kafka consumer lag above 1000 for {{ $labels.consumergroup }}"
```

```yaml
# File: charts/todo-app/templates/dapr/tracing.yaml
# [Skill]: Observability Stack Setup — Dapr Tracing Config

{{- if .Values.dapr.enabled }}
apiVersion: dapr.io/v1alpha1
kind: Configuration
metadata:
  name: tracing-config
  namespace: {{ .Values.global.namespace }}
spec:
  tracing:
    samplingRate: "1"
    zipkin:
      endpointAddress: "http://monitoring-jaeger-collector.monitoring.svc:9411/api/v2/spans"
  metric:
    enabled: true
{{- end }}
```

**Quality Standards**:
- Resource limits on all monitoring components — must fit within OKE always-free / Minikube budget
- Grafana dashboards provisioned as ConfigMaps — not manually created through UI
- Alert rules: pod restarts > 3 in 5min, error rate > 5%, p95 latency > 2s, Kafka lag > 1000
- Loki log retention: 72 hours for Minikube, 7 days for cloud
- Dapr tracing at 100% sampling in dev, 10% in production
- `kubectl port-forward` commands provided for local access to Grafana
- Prometheus scrapes Dapr sidecar metrics port (9090) automatically

---

### 12. Cloud Secrets Management

**Purpose**: Securely manage application secrets (DATABASE_URL, API keys, Kafka credentials, JWT secrets) across Minikube and cloud environments using Dapr Secrets building block backed by Kubernetes Secrets, Azure Key Vault, or OCI Vault.

**Inputs**:
- `secret_store_type`: "kubernetes" (Minikube/default) | "azure-keyvault" | "oci-vault" | "gcp-secretmanager"
- `secrets_list`: List of secret key names to manage
- `deployment_target`: "minikube" or "cloud"

**Outputs**:
- Dapr secret store component YAML
- Kubernetes Secret manifest (for Minikube / base layer)
- Cloud secret store configuration (for cloud targets)
- Application code for retrieving secrets via Dapr

**Implementation Template**:
```yaml
# File: charts/todo-app/templates/secrets.yaml
# [Skill]: Cloud Secrets Management — Kubernetes Secrets (base layer)

apiVersion: v1
kind: Secret
metadata:
  name: todo-app-secrets
  namespace: {{ .Values.global.namespace }}
type: Opaque
data:
  database-url: {{ .Values.secrets.databaseUrl | b64enc | quote }}
  better-auth-secret: {{ .Values.secrets.betterAuthSecret | b64enc | quote }}
  openai-api-key: {{ .Values.secrets.openaiApiKey | b64enc | quote }}
  kafka-username: {{ .Values.secrets.kafkaUsername | default "" | b64enc | quote }}
  kafka-password: {{ .Values.secrets.kafkaPassword | default "" | b64enc | quote }}
```

```yaml
# File: charts/todo-app/templates/dapr/secretstore-azure.yaml
# [Skill]: Cloud Secrets Management — Azure Key Vault via Dapr

{{- if and .Values.dapr.enabled (eq .Values.dapr.secretStore.type "azure-keyvault") }}
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: taskflow-secrets
  namespace: {{ .Values.global.namespace }}
spec:
  type: secretstores.azure.keyvault
  version: v1
  metadata:
    - name: vaultName
      value: {{ .Values.dapr.secretStore.azure.vaultName }}
    - name: azureClientId
      value: {{ .Values.dapr.secretStore.azure.clientId }}
    - name: azureTenantId
      value: {{ .Values.dapr.secretStore.azure.tenantId }}
    - name: azureClientSecret
      secretKeyRef:
        name: azure-sp-secret
        key: client-secret
{{- end }}
```

```python
# File: backend/core/secrets.py
# [Skill]: Cloud Secrets Management — Secret retrieval

import os
import logging

logger = logging.getLogger(__name__)

async def get_secret(key: str) -> str:
    """Retrieve a secret, preferring Dapr when available."""
    use_dapr = os.getenv("USE_DAPR", "false").lower() == "true"

    if use_dapr:
        from backend.dapr.client import dapr_get_secret
        secrets = await dapr_get_secret("taskflow-secrets", key)
        return secrets.get(key, "")
    else:
        # Fallback: read from environment variables
        env_key = key.upper().replace("-", "_")
        value = os.getenv(env_key, "")
        if not value:
            logger.warning(f"Secret '{key}' not found in environment")
        return value
```

**Quality Standards**:
- Never store secrets in plain text in Helm values files committed to git
- Secrets passed via `--set` during `helm install/upgrade` or via sealed-secrets
- Dapr secrets building block abstracts the backend: swap Kubernetes → Azure Key Vault with YAML change only
- Application code uses `get_secret()` function — never reads `os.environ` directly for sensitive values
- Secret rotation: documented procedure for rotating each secret without downtime
- Kubernetes RBAC: only the `todo-app` service account can read `todo-app-secrets`
- GitHub Actions secrets stored in GitHub Secrets — referenced as `${{ secrets.KEY }}`

---

## Skill Composition Patterns

### Pattern 1: Feature-to-Event Pipeline
**Skills**: Schema Migration Extensions → Advanced Search/Filter/Sort → Domain Event Emission → Kafka Producer-Consumer
**Sequence**: Add DB columns → build API endpoints → instrument with events → wire consumers
**Use case**: Implementing any new feature (priorities, tags, due dates, recurrence, reminders)

### Pattern 2: Dapr-First Infrastructure
**Skills**: Dapr Component Setup → Kafka Topic Management → Helm Dapr Sidecar Injection → Event-Driven Service Creation
**Sequence**: Define Dapr components → create topics → annotate deployments → deploy consumer services
**Use case**: Setting up the event-driven architecture layer from scratch

### Pattern 3: Local-to-Cloud Deployment
**Skills**: Helm Dapr Sidecar Injection → Cloud Cluster Provisioning → Cloud Secrets Management → GitHub Actions CI/CD → Observability Stack Setup
**Sequence**: Update Helm charts → provision cluster → configure secrets → automate pipeline → add monitoring
**Use case**: Migrating from Minikube local deployment to production cloud Kubernetes

### Pattern 4: End-to-End Feature Delivery
**Skills**: Schema Migration Extensions → Advanced Search/Filter/Sort → Domain Event Emission → Event-Driven Service Creation → Helm Dapr Sidecar Injection → GitHub Actions CI/CD
**Sequence**: Full SDD cycle from database to deployment for a single feature
**Use case**: Complete feature implementation using the Agentic Dev Stack workflow

---

## Skill Usage by Agent

| Agent | Primary Skills | Secondary Skills |
|-------|---------------|------------------|
| **1. Feature Developer** | Schema Migration Extensions, Advanced Search/Filter/Sort, Domain Event Emission | Kafka Producer-Consumer |
| **2. Event-Driven Architecture** | Kafka Topic Management, Kafka Producer-Consumer, Domain Event Emission | Event-Driven Service Creation |
| **3. Dapr Integration** | Dapr Component Setup, Cloud Secrets Management | Helm Dapr Sidecar Injection |
| **4. Local Deployment** | Helm Dapr Sidecar Injection, Kafka Topic Management | Dapr Component Setup, Observability Stack Setup |
| **5. Cloud Deployment** | Cloud Cluster Provisioning, Cloud Secrets Management | Helm Dapr Sidecar Injection |
| **6. CI/CD Pipeline** | GitHub Actions CI/CD | Cloud Cluster Provisioning |
| **7. Monitoring & Logging** | Observability Stack Setup | Dapr Component Setup (tracing) |

---

## Phase V Skill Requirements

### Must-Haves
- All 12 skills must produce outputs that pass automated validation (linting, type checking, dry-run)
- Every skill builds on Phase III (FastAPI + SQLModel + MCP) and Phase IV (Minikube + Helm) artifacts
- Skills that produce Kubernetes YAML must pass `kubectl apply --dry-run=client` validation
- Skills that produce Python code must pass `ruff check` and `mypy --strict` where applicable
- Event schemas are versioned (`schema_version` field) from day one
- All secrets management follows Dapr abstraction — no direct cloud SDK calls in application code

### Quality Gates
- **Schema Migration**: `alembic upgrade head` + `alembic downgrade -1` both succeed; existing tests pass
- **API Endpoints**: 100% user_id isolation; no query returns cross-user data; pagination defaults applied
- **Kafka Topics**: Topics created and verified via `kafka-topics --describe`; schemas validated with test events
- **Kafka Producers/Consumers**: At-least-once delivery verified; idempotent consumers tested with duplicate events
- **Dapr Components**: All components healthy via `dapr components -k`; swappability tested (change backend, verify app still works)
- **Event-Driven Services**: Subscription endpoints return correct Dapr response codes; dead-letter handling tested
- **Domain Events**: Events emitted only after DB commit; emission failure does not block CRUD
- **Helm Charts**: `helm lint` passes; `helm template` renders without errors; Dapr annotations conditional on toggle
- **Cloud Clusters**: `kubectl get nodes` shows ready nodes; Dapr system pods running; ingress controller responding
- **CI/CD Pipeline**: Full pipeline runs in under 15 minutes; `--atomic` rollback tested; rollback workflow functional
- **Observability**: Grafana accessible; Prometheus scraping all targets; alert rules firing on test conditions
- **Secrets**: No plaintext secrets in any committed file; Dapr secret retrieval tested; rotation documented
