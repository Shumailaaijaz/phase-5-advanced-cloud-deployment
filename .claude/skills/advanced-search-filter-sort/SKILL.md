---
name: advanced-search-filter-sort
description: Implement API endpoints and query builders for searching tasks by keyword, filtering by priority/tags/status/due date range, and sorting by any field with pagination. Use when building the enhanced tasks listing endpoint for Phase V intermediate features.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
---

# Advanced Search, Filter, and Sort

## Purpose

Implement API endpoints and query builders for searching tasks by keyword, filtering by priority/tags/status/due date range, and sorting by any field. Extends the existing FastAPI tasks router with query parameter composition and pagination.

## Used by

- Feature Developer Agent (Agent 1)
- full-stack-backend agent

## When to Use

- Adding keyword search across task title and description
- Implementing priority, status, or tag-based filtering
- Adding due date range filters
- Enabling multi-field sorting (created_at, due_at, priority, title)
- Implementing cursor-based or offset pagination

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `filter_fields` | list | Yes | Fields to filter by (priority, status, tag, due_at) |
| `sort_fields` | list | Yes | Fields to sort by (created_at, due_at, priority, title) |
| `search_fields` | list | Yes | Fields for keyword search (title, description) |
| `existing_router_path` | string | Yes | Path to current tasks API router |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| Updated endpoint | Python | FastAPI endpoint with query parameters |
| Query builder | Python | Composable SQLModel filter utility |
| Pydantic models | Python | Filter/sort request validation |
| Pagination | JSON | Offset/limit response with total count |

## Procedure

### Step 1: Define Query Parameters

```python
@router.get("/")
async def list_tasks(
    user_id: str = Depends(get_current_user_id),
    q: Optional[str] = Query(None),
    priority: Optional[str] = Query(None, regex="^P[1-4]$"),
    status: Optional[str] = Query(None, regex="^(pending|completed)$"),
    tag: Optional[List[str]] = Query(None),
    due_after: Optional[datetime] = Query(None),
    due_before: Optional[datetime] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
```

### Step 2: Build Composable Query

Always start with `WHERE user_id = :user_id`, then chain filters.

### Step 3: Paginate and Return

Return `{"tasks": [...], "total": N, "offset": N, "limit": N}`.

## Quality Standards

- [ ] All queries include `WHERE user_id = :user_id` — no cross-user leaks
- [ ] SQL injection impossible via SQLModel parameterized queries
- [ ] Invalid filter values rejected by Pydantic before reaching DB
- [ ] Pagination: offset=0, limit=20 defaults, max limit=100
- [ ] Empty results return `{"tasks": [], "total": 0}` — never 404
- [ ] Indexed columns used in WHERE and ORDER BY clauses
