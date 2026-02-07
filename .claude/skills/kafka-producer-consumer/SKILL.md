---
name: kafka-producer-consumer
description: Implement async Kafka producers and consumers using aiokafka with at-least-once delivery, idempotent processing, dead-letter queues, and graceful shutdown. Use when building the event pipeline services (Notification, Recurring Task, Audit, WebSocket).
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Kafka Producer-Consumer

## Purpose

Implement Kafka producers (in Chat API / MCP Tools) and consumers (Notification Service, Recurring Task Service, Audit Service, WebSocket Service) using `aiokafka` for async Python. Ensures at-least-once delivery, idempotent consumers, and dead-letter queue handling.

## Used by

- Event-Driven Architecture Agent (Agent 2)
- Feature Developer Agent (Agent 1) — producer integration

## When to Use

- Creating an event producer for the Chat API or MCP Tools
- Building consumer services for task-events, reminders, task-updates topics
- Implementing dead-letter queue handling for failed messages
- Adding health checks to consumer services
- Configuring consumer groups for parallel processing

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `role` | string | Yes | "producer" or "consumer" |
| `topic` | string | Yes | Kafka topic name |
| `event_schema` | string | Yes | Event dataclass reference |
| `consumer_group` | string | For consumers | Consumer group ID |
| `connection_config` | dict | Yes | Bootstrap servers, SASL (from env) |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Producer class | Python | Async producer with `publish()` and error handling |
| Consumer class | Python | Base consumer with message loop and shutdown |
| DLQ handler | Python | Dead-letter queue for failed messages |
| Health check | Python | Readiness endpoint for consumer |

## Procedure

### Step 1: Producer Implementation

```python
class EventProducer:
    async def start(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            acks="all",
            retries=3,
        )
        await self._producer.start()

    async def publish_task_event(self, event_type, task_id, user_id, task_data):
        event = TaskEvent.create(event_type, task_id, user_id, task_data)
        await self._producer.send_and_wait(
            topic="task-events",
            value=event.to_json(),
            key=user_id.encode("utf-8"),
        )
```

### Step 2: Consumer Base Class

```python
class BaseConsumer(ABC):
    async def run(self):
        async for msg in self._consumer:
            event = self.deserialize(msg.value)
            if event["event_id"] not in self._processed_ids:
                await self.handle(event)
                self._processed_ids.add(event["event_id"])
            await self._consumer.commit()

    @abstractmethod
    async def handle(self, event: dict): ...
```

### Step 3: Implement Specific Consumers

- `RecurringTaskConsumer`: listens to task-events, creates next occurrence
- `NotificationConsumer`: listens to reminders, sends notifications
- `AuditConsumer`: listens to task-events, stores audit log

## Quality Standards

- [ ] Producers use `acks="all"` and `send_and_wait()` for durable writes
- [ ] Consumers use manual commit after successful processing
- [ ] Idempotency via `event_id` tracking in consumer
- [ ] Dead-letter queue handler for failed messages
- [ ] Graceful shutdown on SIGTERM
- [ ] Credentials from environment variables, never hardcoded
- [ ] Consumer group IDs unique per service
- [ ] Health check returns unhealthy if consumer loop not running
