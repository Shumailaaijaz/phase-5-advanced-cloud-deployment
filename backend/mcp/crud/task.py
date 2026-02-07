"""MCP Task CRUD Operations

Database operations for MCP tools. ALL operations filter by user_id.
"""

from typing import List, Optional
from datetime import datetime
from sqlmodel import Session, select

from models.user import Task
from mcp.schemas.params import AddTaskParams, UpdateTaskParams


def create_task(session: Session, user_id: int, params: AddTaskParams) -> Task:
    """Create a new task for the user.

    Args:
        session: Database session
        user_id: Owner's user ID (integer from DB)
        params: Task creation parameters

    Returns:
        Created Task instance
    """
    task = Task(
        user_id=user_id,
        title=params.title,
        description=params.description,
        priority=params.priority or "Medium",
        due_date=params.due_date,
        completed=False,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_tasks_for_user(session: Session, user_id: int) -> List[Task]:
    """Retrieve all tasks for a user, ordered by created_at DESC.

    Args:
        session: Database session
        user_id: Owner's user ID

    Returns:
        List of Task instances (empty if none)
    """
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_task_by_id_and_user(session: Session, task_id: int, user_id: int) -> Optional[Task]:
    """Retrieve a specific task by ID, ensuring user ownership.

    Args:
        session: Database session
        task_id: Task ID to lookup
        user_id: Owner's user ID

    Returns:
        Task instance if found and owned by user, None otherwise
    """
    statement = (
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == user_id)
    )
    return session.exec(statement).first()


def update_task(session: Session, task: Task, params: UpdateTaskParams) -> Task:
    """Update task attributes.

    Args:
        session: Database session
        task: Task instance to update
        params: Update parameters (only non-None fields are applied)

    Returns:
        Updated Task instance
    """
    if params.title is not None:
        task.title = params.title
    if params.description is not None:
        task.description = params.description
    if params.priority is not None:
        task.priority = params.priority
    if params.due_date is not None:
        task.due_date = params.due_date
    if params.completed is not None:
        task.completed = params.completed

    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task: Task) -> None:
    """Delete a task from the database.

    Args:
        session: Database session
        task: Task instance to delete
    """
    session.delete(task)
    session.commit()
