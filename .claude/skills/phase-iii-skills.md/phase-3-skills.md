# Phase III Skills — AI Chatbot Integration

## Overview

Phase III extends the full-stack Todo web application from Phase II by integrating an AI-powered chatbot for managing todos through natural language. This phase leverages the MCP (Model Context Protocol) server architecture, OpenAI Agents SDK, and Claude Code/Spec-Kit Plus for development. Skills build upon Phase II's web and API foundations, focusing on AI agents, tool exposure, stateless conversations, and database-persisted state.

Development follows the Agentic Dev Stack: Write spec → Generate plan → Break into tasks → Implement via Claude Code. No manual coding; all implementation is AI-generated and reviewed.

---

## 🎯 Core Skills Catalog

### 1. MCP Tool Creation Skill

**Purpose**: Define and implement MCP tools for task operations, exposing them as stateless functions with database persistence.

**Inputs**:
- `tool_name`: Name of the tool (e.g., "add_task")
- `parameters_schema`: JSON schema for input parameters
- `return_schema`: JSON schema for output
- `database_model`: Reference to relevant SQLModel model (e.g., Task)

**Outputs**:
- `tool_function`: Python function code
- `tool_schema`: OpenAI-compatible tool schema (JSON)
- `is_stateless`: Boolean (always true, confirms no in-memory state)

**Implementation Template**:
```python
# File: mcp/tools/add_task.py
# [Skill]: MCP Tool Creation

from sqlmodel import Session, select
from app.models import Task
from app.database import engine
from typing import Optional, Dict

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
    with Session(engine) as session:
        new_task = Task(user_id=user_id, title=title, description=description)
        session.add(new_task)
        session.commit()
        session.refresh(new_task)
        return {
            "task_id": new_task.id,
            "status": "created",
            "title": title
        }