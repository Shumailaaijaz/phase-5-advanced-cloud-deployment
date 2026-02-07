---
name: domain-event-emission
description: Integrate event publishing hooks into existing CRUD operations and MCP Tools. Every task create/update/complete/delete emits a TaskEvent via Dapr Pub/Sub or direct aiokafka. Reminder events emitted when due dates are set. Use when instrumenting existing code with event-driven capabilities.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Domain Event Emission

## Purpose

Integrate event publishing hooks into existing CRUD operations in the Chat API and MCP Tools. Every task create/update/complete/delete emits a `TaskEvent` to Kafka (via Dapr Pub/Sub or direct aiokafka). Reminder events are emitted when due dates are set.

## Used by

- Feature Developer Agent (Agent 1)
- Event-Driven Architecture Agent (Agent 2)

## When to Use

- Instrumenting existing add_task, update_task, complete_task, delete_task with events
- Publishing reminder events when due_at and remind_before_minutes are set
- Configuring Dapr vs direct Kafka event transport
- Testing that events are emitted correctly after DB commits

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | CRUD operation (create, update, complete, delete) |
| `existing_code_path` | string | Yes | Path to CRUD function or MCP tool |
| `event_schema` | string | Yes | Event dataclass (TaskEvent, ReminderEvent) |
| `publish_method` | string | Yes | "dapr" or "direct" (aiokafka) |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Modified CRUD function | Python | Function with event emission after commit |
| Event emitter helper | Python | Unified emit function (Dapr/direct toggle) |
| Config toggle | Python | USE_DAPR setting for transport selection |

## Procedure

### Step 1: Create Unified Emitter

```python
async def emit_task_event(event_type, task_id, user_id, task_data):
    event = TaskEvent.create(event_type, task_id, user_id, task_data)
    if settings.USE_DAPR:
        await dapr_publish("taskflow-pubsub", "task-events", event.__dict__)
    else:
        await event_producer.publish_task_event(...)
```

### Step 2: Instrument CRUD Operations

```python
# In add_task — AFTER session.commit()
await emit_task_event("created", str(new_task.id), user_id, task_dict)
await emit_reminder_if_needed(new_task, user_id)
```

### Step 3: Reminder Emission

```python
async def emit_reminder_if_needed(task, user_id):
    if not task.due_at or not task.remind_before_minutes:
        return
    remind_at = task.due_at - timedelta(minutes=task.remind_before_minutes)
    # Publish reminder event...
```

## Quality Standards

- [ ] Events emitted AFTER successful DB commit — never before
- [ ] Event emission failure does NOT fail the CRUD operation (fire-and-forget)
- [ ] USE_DAPR toggle switches transport — same event schemas either way
- [ ] Every modified function has event emission tested (mock producer)
- [ ] Reminder events only when both due_at AND remind_before_minutes are set
- [ ] Task data in events is minimal (ID, title, status, changes) — not full DB row
