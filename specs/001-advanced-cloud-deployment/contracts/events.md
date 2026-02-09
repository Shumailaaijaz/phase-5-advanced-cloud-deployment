# Event Contracts: Phase V Kafka Schemas

**Date**: 2026-02-07 | **Spec**: [../spec.md](../spec.md)

---

## Topics

| Topic | Retention | Partitions | Partition Key | Consumer Group |
| ----- | --------- | ---------- | ------------- | -------------- |
| `task-events` | 7 days | 3 | `user_id` | `recurring-svc`, `audit-svc` |
| `reminders` | 1 day | 1 | `user_id` | `notification-svc` |
| `task-updates` | 1 hour | 3 | `user_id` | `sync-svc` |

---

## TaskEvent Schema (v1.0)

Published to `task-events` and `task-updates` topics.

```json
{
  "event_id": "550e8400-e29b-41d4-a716-446655440000",
  "event_type": "task.created",
  "user_id": "42",
  "task_id": 123,
  "data": {
    "title": "Weekly standup",
    "priority": "P1",
    "tags": ["work", "meetings"],
    "due_date": "2026-02-10T09:00:00Z",
    "recurrence_rule": "weekly",
    "completed": false
  },
  "schema_version": "1.0",
  "timestamp": "2026-02-07T14:30:00Z"
}
```

**Event Types**: `task.created`, `task.updated`, `task.completed`, `task.deleted`

**Invariants**:
- `event_id` is UUID4, globally unique
- `timestamp` is ISO 8601 UTC
- `data` contains only fields relevant to the event type (e.g., `task.deleted` has minimal data)
- Published ONLY after successful `session.commit()`

---

## ReminderEvent Schema (v1.0)

Published to `reminders` topic by the cron binding handler.

```json
{
  "event_id": "660e8400-e29b-41d4-a716-446655440001",
  "event_type": "reminder.due",
  "user_id": "42",
  "task_id": 123,
  "data": {
    "title": "Weekly standup",
    "due_date": "2026-02-10T09:00:00Z",
    "reminder_minutes": 30
  },
  "schema_version": "1.0",
  "timestamp": "2026-02-10T08:30:00Z"
}
```

**Invariants**:
- Only published for tasks with `reminder_sent = false AND completed = false`
- After consumer processes: `reminder_sent` set to `true` in DB
- Idempotent: duplicate `event_id` → skip processing

---

## Consumer Contracts

### Recurring Task Service

- **Subscribes**: `task-events` (filter: `event_type = "task.completed"`)
- **Action**: If `data.recurrence_rule` is set and `recurrence_depth < 1000`, create next task occurrence
- **Publishes**: `task.created` event for the new task
- **Idempotency**: Track `event_id` in processed set; skip duplicates

### Notification Service

- **Subscribes**: `reminders`
- **Action**: Send notification to user, set `reminder_sent = true`
- **Idempotency**: Check `event_id`; check `reminder_sent` flag before processing

### Audit Logger

- **Subscribes**: `task-events` (all event types)
- **Action**: Insert into `audit_log` table with `event_id` as unique key
- **Idempotency**: UNIQUE constraint on `event_id` — duplicate insert is no-op

### Real-time Sync

- **Subscribes**: `task-updates`
- **Action**: Push update to connected frontend clients (SSE or WebSocket)
- **Idempotency**: Last-write-wins based on `timestamp`
