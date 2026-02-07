---
name: mcp-tool-creation
description: Define and implement MCP tools for task operations, exposing them as stateless functions with database persistence. Use when implementing MCP server tools for the AI chatbot integration.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# MCP Tool Creation Skill

## Purpose

Define and implement MCP (Model Context Protocol) tools for task operations, exposing them as stateless functions with database persistence. This skill ensures all MCP tools follow a consistent pattern with proper user isolation, error handling, and OpenAI-compatible schemas.

## Used by

- mcp-server-specialist agent
- mcp-architect agent
- ai-agent-designer agent

## When to Use

- Implementing new MCP tools for the task management chatbot
- Creating CRUD operations (add_task, list_tasks, complete_task, delete_task, update_task)
- Exposing database operations as stateless MCP functions
- Generating OpenAI-compatible tool schemas for agent integration

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `tool_name` | string | Yes | Name of the tool (e.g., "add_task", "list_tasks") |
| `parameters_schema` | JSON object | Yes | JSON schema for input parameters |
| `return_schema` | JSON object | Yes | JSON schema for output |
| `database_model` | string | Yes | Reference to relevant SQLModel model (e.g., Task) |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `tool_function` | Python code | Complete Python function implementation |
| `tool_schema` | JSON | OpenAI-compatible tool schema |
| `is_stateless` | boolean | Always true, confirms no in-memory state |

## Implementation Template

```python
# File: mcp/tools/{tool_name}.py
# [Skill]: MCP Tool Creation

from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

def {tool_name}(user_id: str, **kwargs) -> Dict:
    """
    {Tool description}.

    Args:
        user_id: User's identifier (required for isolation)
        **kwargs: Tool-specific parameters

    Returns:
        Dict with operation result

    Raises:
        ValueError: For invalid inputs
    """
    logger.info(f"Tool invocation: {tool_name} for user {user_id}")

    # Validate required inputs
    if not user_id:
        raise ValueError("user_id is required")

    with Session(engine) as session:
        # Tool-specific implementation
        # Always filter by user_id for isolation
        pass
```

## Standard Tool Implementations

### add_task

```python
# File: mcp/tools/add_task.py
from sqlmodel import Session
from app.models import Task
from app.database import engine
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

def add_task(user_id: str, title: str, description: Optional[str] = None) -> Dict:
    """
    Create a new task for the user.

    Args:
        user_id: User's identifier
        title: Task title
        description: Optional task description

    Returns:
        Dict with task_id, status, title
    """
    logger.info(f"add_task invoked for user {user_id}")

    if not title or not title.strip():
        raise ValueError("title is required and cannot be empty")

    with Session(engine) as session:
        new_task = Task(
            user_id=user_id,
            title=title.strip(),
            description=description.strip() if description else None
        )
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return {
            "task_id": new_task.id,
            "status": "created",
            "title": new_task.title
        }
```

### list_tasks

```python
# File: mcp/tools/list_tasks.py
from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

def list_tasks(user_id: str, status_filter: Optional[str] = None) -> Dict:
    """
    List all tasks for the user.

    Args:
        user_id: User's identifier
        status_filter: Optional filter by status ("pending", "completed")

    Returns:
        Dict with tasks list and count
    """
    logger.info(f"list_tasks invoked for user {user_id}")

    with Session(engine) as session:
        query = select(Task).where(Task.user_id == user_id)

        if status_filter:
            query = query.where(Task.status == status_filter)

        tasks = session.exec(query).all()

        return {
            "tasks": [
                {
                    "task_id": task.id,
                    "title": task.title,
                    "description": task.description,
                    "status": task.status,
                    "created_at": task.created_at.isoformat() if task.created_at else None
                }
                for task in tasks
            ],
            "count": len(tasks)
        }
```

### complete_task

```python
# File: mcp/tools/complete_task.py
from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def complete_task(user_id: str, task_id: str) -> Dict:
    """
    Mark a task as completed.

    Args:
        user_id: User's identifier
        task_id: ID of the task to complete

    Returns:
        Dict with task_id and new status
    """
    logger.info(f"complete_task invoked for user {user_id}, task {task_id}")

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            raise ValueError(f"Task {task_id} not found for user")

        task.status = "completed"
        session.add(task)
        session.commit()
        session.refresh(task)

        return {
            "task_id": task.id,
            "status": task.status,
            "title": task.title
        }
```

### delete_task

```python
# File: mcp/tools/delete_task.py
from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Dict
import logging

logger = logging.getLogger(__name__)

def delete_task(user_id: str, task_id: str) -> Dict:
    """
    Delete a task.

    Args:
        user_id: User's identifier
        task_id: ID of the task to delete

    Returns:
        Dict with task_id and status
    """
    logger.info(f"delete_task invoked for user {user_id}, task {task_id}")

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            raise ValueError(f"Task {task_id} not found for user")

        session.delete(task)
        session.commit()

        return {
            "task_id": task_id,
            "status": "deleted"
        }
```

### update_task

```python
# File: mcp/tools/update_task.py
from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

def update_task(
    user_id: str,
    task_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None
) -> Dict:
    """
    Update a task's title or description.

    Args:
        user_id: User's identifier
        task_id: ID of the task to update
        title: New title (optional)
        description: New description (optional)

    Returns:
        Dict with updated task details
    """
    logger.info(f"update_task invoked for user {user_id}, task {task_id}")

    if not title and description is None:
        raise ValueError("At least one of title or description must be provided")

    with Session(engine) as session:
        task = session.exec(
            select(Task).where(Task.id == task_id, Task.user_id == user_id)
        ).first()

        if not task:
            raise ValueError(f"Task {task_id} not found for user")

        if title:
            task.title = title.strip()
        if description is not None:
            task.description = description.strip() if description else None

        session.add(task)
        session.commit()
        session.refresh(task)

        return {
            "task_id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status
        }
```

## Tool Schema Templates (OpenAI-compatible)

```python
# File: mcp/schemas/tool_schemas.py

add_task_schema = {
    "type": "function",
    "function": {
        "name": "add_task",
        "description": "Create a new task for the user",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User's unique identifier"
                },
                "title": {
                    "type": "string",
                    "description": "Task title"
                },
                "description": {
                    "type": "string",
                    "description": "Optional task description"
                }
            },
            "required": ["user_id", "title"]
        }
    }
}

list_tasks_schema = {
    "type": "function",
    "function": {
        "name": "list_tasks",
        "description": "List all tasks for the user, optionally filtered by status",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User's unique identifier"
                },
                "status_filter": {
                    "type": "string",
                    "enum": ["pending", "completed"],
                    "description": "Optional filter by task status"
                }
            },
            "required": ["user_id"]
        }
    }
}

complete_task_schema = {
    "type": "function",
    "function": {
        "name": "complete_task",
        "description": "Mark a task as completed",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User's unique identifier"
                },
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to complete"
                }
            },
            "required": ["user_id", "task_id"]
        }
    }
}

delete_task_schema = {
    "type": "function",
    "function": {
        "name": "delete_task",
        "description": "Delete a task permanently",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User's unique identifier"
                },
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to delete"
                }
            },
            "required": ["user_id", "task_id"]
        }
    }
}

update_task_schema = {
    "type": "function",
    "function": {
        "name": "update_task",
        "description": "Update a task's title or description",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User's unique identifier"
                },
                "task_id": {
                    "type": "string",
                    "description": "ID of the task to update"
                },
                "title": {
                    "type": "string",
                    "description": "New task title"
                },
                "description": {
                    "type": "string",
                    "description": "New task description"
                }
            },
            "required": ["user_id", "task_id"]
        }
    }
}

# All tools collection
ALL_TOOL_SCHEMAS = [
    add_task_schema,
    list_tasks_schema,
    complete_task_schema,
    delete_task_schema,
    update_task_schema
]
```

## Quality Standards

### Statelessness

- Each function call creates its own database session
- No global variables or shared state between calls
- Session is closed after each operation via context manager

### Error Handling

- Raise `ValueError` for invalid inputs with clear messages
- Always check if resource exists before operating on it
- Never expose internal errors to clients

### SQL Injection Safety

- Use SQLModel's parameterized queries exclusively
- Never concatenate user input into SQL strings
- All queries use SQLModel's type-safe query builder

### User Isolation

- Always filter by `user_id` in all database queries
- Never allow cross-user data access
- Validate `user_id` is present before any operation

### Logging

- Log tool invocation with user_id (not sensitive data)
- Log errors with sufficient context for debugging
- Use structured logging format

## Verification Checklist

When creating a new MCP tool, verify:

- [ ] Function accepts `user_id` as first parameter
- [ ] All database queries filter by `user_id`
- [ ] Function uses `with Session(engine)` context manager
- [ ] No global/module-level state is modified
- [ ] Input validation raises `ValueError` with clear messages
- [ ] Return type is `Dict` with documented structure
- [ ] OpenAI-compatible schema is defined
- [ ] Logging is implemented at INFO level
- [ ] Docstring documents all parameters and return values

## Output Format

When generating an MCP tool, output:

1. **Python function code** in `mcp/tools/{tool_name}.py`
2. **Tool schema** in `mcp/schemas/tool_schemas.py`
3. **Confirmation** that `is_stateless = True`
