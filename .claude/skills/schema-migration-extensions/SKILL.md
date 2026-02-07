---
name: schema-migration-extensions
description: Extend SQLModel Task model with priorities (P1-P4), tags (many-to-many), due dates (timezone-aware), recurrence rules, and reminders. Generate reversible Alembic migrations for Neon PostgreSQL. Use when implementing Phase V advanced features that require database schema changes.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Schema Migration Extensions

## Purpose

Extend the existing SQLModel Task model and Neon PostgreSQL schema with columns and tables for priorities (P1-P4), tags (many-to-many), due dates (timezone-aware), recurrence rules (daily/weekly/monthly/custom cron), and reminders (configurable lead times). Generate Alembic migrations that are safe, reversible, and compatible with existing data.

## Used by

- Feature Developer Agent (Agent 1)
- Event-Driven Architecture Agent (Agent 2) — for event schema alignment
- database-specialist agent

## When to Use

- Adding priority levels (P1-P4) to the Task model
- Creating a many-to-many tags system with per-user isolation
- Adding timezone-aware due date columns
- Implementing recurrence rules (daily/weekly/monthly/custom cron)
- Adding reminder configuration (lead time in minutes, sent flag)
- Any Phase V feature that requires new columns, tables, or relationships

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `feature_name` | string | Yes | Feature being added (e.g., "priorities", "tags") |
| `model_changes` | string | Yes | Description of new columns, tables, or relationships |
| `existing_model_path` | string | Yes | Path to current SQLModel model file |
| `migration_message` | string | Yes | Descriptive Alembic migration message |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Updated model file | Python | SQLModel model with new fields and relationships |
| Alembic migration | Python | Migration script with upgrade() and downgrade() |
| Pydantic schemas | Python | Updated request/response models |
| Verification | boolean | Migration is reversible |

## Procedure

### Step 1: Read Existing Model

Read the current Task model and identify existing fields to avoid conflicts.

### Step 2: Add New Fields

Add columns with `nullable=True` and sensible defaults for backward compatibility:

```python
# Priority enum
class Priority(str, Enum):
    P1 = "P1"  # Critical
    P2 = "P2"  # High
    P3 = "P3"  # Medium
    P4 = "P4"  # Low

# New Task fields
priority: Optional[Priority] = Field(default=None, index=True)
due_at: Optional[datetime] = Field(
    default=None,
    sa_column=sa.Column(sa.DateTime(timezone=True), nullable=True, index=True)
)
recurrence_rule: Optional[str] = Field(default=None)
cron_expression: Optional[str] = Field(default=None, max_length=100)
remind_before_minutes: Optional[int] = Field(default=None)
reminder_sent: bool = Field(default=False)
```

### Step 3: Create Tag Model and Link Table

```python
class TaskTagLink(SQLModel, table=True):
    task_id: str = Field(foreign_key="tasks.id", primary_key=True)
    tag_id: str = Field(foreign_key="tags.id", primary_key=True)

class Tag(SQLModel, table=True):
    id: Optional[str] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    name: str = Field(max_length=50)
    color: Optional[str] = Field(default=None, max_length=7)
```

### Step 4: Generate Alembic Migration

```bash
cd backend
alembic revision --autogenerate -m "add priorities tags recurrence reminders"
alembic upgrade head       # Test upgrade
alembic downgrade -1       # Test downgrade
alembic upgrade head       # Re-apply
```

### Step 5: Verify

```bash
# Run existing tests
pytest backend/tests/ -q
# Verify migration reversibility
alembic downgrade -1 && alembic upgrade head
```

## Quality Standards

- [ ] Every migration has both `upgrade()` and `downgrade()` functions
- [ ] New columns are `nullable=True` with sensible defaults
- [ ] Indexes on columns used in WHERE clauses (priority, due_at, user_id)
- [ ] Unique constraints at DB level (e.g., user_id + tag name)
- [ ] `alembic upgrade head` and `alembic downgrade -1` both pass
- [ ] Existing tests still pass after migration
- [ ] No data loss: existing rows remain valid after migration

## Output Format

1. **Updated model file** — full Python code for modified models
2. **Alembic migration** — complete upgrade/downgrade script
3. **Pydantic schemas** — request/response models for new fields
4. **Verification commands** — alembic and pytest commands to confirm
