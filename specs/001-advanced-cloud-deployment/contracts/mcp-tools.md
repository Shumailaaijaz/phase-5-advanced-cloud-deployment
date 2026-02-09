# MCP Tool Contracts: Phase V Extensions

**Date**: 2026-02-07 | **Spec**: [../spec.md](../spec.md)

---

## add_task (Extended)

**New Parameters**:

| Parameter | Type | Required | Default | Validation |
| --------- | ---- | -------- | ------- | ---------- |
| priority | string | No | "P3" | One of: P1, P2, P3, P4 |
| due_date | string | No | null | ISO 8601 datetime |
| tags | string[] | No | [] | Max 10 items, each 1-50 chars |
| recurrence_rule | string | No | null | daily/weekly/monthly/cron |
| reminder_minutes | integer | No | null | 0-10080 |

**Response**: Existing `TaskData` extended with `priority`, `due_date`, `tags`, `recurrence_rule`, `reminder_minutes`

**Post-Commit Event**: `task.created` → `task-events` topic

---

## update_task (Extended)

**New Parameters**: Same as `add_task` new params (all optional). Additionally:
- Setting `tags` replaces all existing tags on the task
- Setting `due_date` resets `reminder_sent` to false
- Setting `recurrence_rule` to null stops future auto-creation

**Post-Commit Event**: `task.updated` → `task-events` topic

---

## complete_task (Extended)

**Existing behavior unchanged.** New post-commit:

**Post-Commit Event**: `task.completed` → `task-events` topic
- If `recurrence_rule` is set, Recurring Task Service creates next occurrence

---

## delete_task (Extended)

**Existing behavior unchanged.** New post-commit:

**Post-Commit Event**: `task.deleted` → `task-events` topic

---

## list_tasks (Major Extension)

**New Parameters**:

| Parameter | Type | Required | Default | Validation |
| --------- | ---- | -------- | ------- | ---------- |
| search | string | No | null | Max 200 chars |
| completed | boolean | No | null | true/false |
| priority | string | No | null | P1/P2/P3/P4 |
| tag | string | No | null | Exact match, lowercase |
| due_before | string | No | null | ISO 8601 date |
| due_after | string | No | null | ISO 8601 date |
| has_reminder | boolean | No | null | true/false |
| is_overdue | boolean | No | null | true/false |
| sort_by | string | No | "created_at" | created_at/updated_at/due_date/priority/title |
| sort_order | string | No | "desc" | asc/desc |
| page | integer | No | 1 | >= 1 |
| page_size | integer | No | 10 | 1-100 |

**Response**: Extended with pagination metadata:

```json
{
  "status": "ok",
  "data": {
    "tasks": [...],
    "total_count": 42,
    "page": 1,
    "page_size": 10,
    "total_pages": 5
  }
}
```

---

## list_tags (New Tool)

**Parameters**:

| Parameter | Type | Required | Validation |
| --------- | ---- | -------- | ---------- |
| user_id | string | Yes | Non-empty |

**Response**:

```json
{
  "status": "ok",
  "data": {
    "tags": [
      {"id": 1, "name": "work", "task_count": 5},
      {"id": 2, "name": "personal", "task_count": 3}
    ]
  }
}
```

---

## list_recurring_tasks (New Tool)

**Parameters**:

| Parameter | Type | Required | Validation |
| --------- | ---- | -------- | ---------- |
| user_id | string | Yes | Non-empty |

**Response**: Same as `list_tasks` but filtered to `recurrence_rule IS NOT NULL`
