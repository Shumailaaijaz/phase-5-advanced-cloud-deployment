"""MCP Task CRUD Operations

Database operations for MCP tools. ALL operations filter by user_id.
"""

from typing import List, Optional, Tuple
from datetime import datetime
from sqlmodel import Session, select, func, text, col
import sqlalchemy as sa

from models.user import Task
from models.tag import Tag, TaskTag
from mcp.schemas.params import AddTaskParams, UpdateTaskParams, ListTasksParams


def _sync_tags(session: Session, task_id: int, user_id: int, tag_names: List[str]) -> None:
    """Sync tags for a task — create missing tags, link via task_tag junction."""
    # Remove existing task_tag links
    session.exec(
        sa.delete(TaskTag).where(TaskTag.task_id == task_id)
    )

    if not tag_names:
        return

    for name in tag_names:
        # Find or create tag for this user
        tag = session.exec(
            select(Tag).where(Tag.user_id == user_id, Tag.name == name)
        ).first()

        if tag is None:
            tag = Tag(name=name, user_id=user_id, created_at=datetime.utcnow())
            session.add(tag)
            session.flush()  # Get tag.id

        # Create junction row
        task_tag = TaskTag(task_id=task_id, tag_id=tag.id)
        session.add(task_tag)


def _get_tags_for_task(session: Session, task_id: int) -> List[str]:
    """Get tag names for a task."""
    stmt = (
        select(Tag.name)
        .join(TaskTag, Tag.id == TaskTag.tag_id)
        .where(TaskTag.task_id == task_id)
        .order_by(Tag.name)
    )
    return list(session.exec(stmt).all())


def create_task(session: Session, user_id: int, params: AddTaskParams) -> Task:
    """Create a new task for the user."""
    task = Task(
        user_id=user_id,
        title=params.title,
        description=params.description,
        priority=params.priority or "P3",
        due_date=datetime.fromisoformat(params.due_date) if params.due_date else None,
        completed=False,
        recurrence_rule=params.recurrence_rule,
        reminder_minutes=params.reminder_minutes,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    session.add(task)
    session.flush()  # Get task.id for tag sync

    # Sync tags if provided
    if params.tags:
        _sync_tags(session, task.id, user_id, params.tags)

    session.commit()
    session.refresh(task)
    return task


def get_tasks_for_user(session: Session, user_id: int) -> List[Task]:
    """Retrieve all tasks for a user, ordered by created_at DESC."""
    statement = (
        select(Task)
        .where(Task.user_id == user_id)
        .order_by(Task.created_at.desc())
    )
    return list(session.exec(statement).all())


def get_tasks_filtered(
    session: Session,
    user_id: int,
    params: ListTasksParams,
) -> Tuple[List[Task], int]:
    """Retrieve tasks with search, filters, sort, and pagination.

    Returns (tasks, total_count).
    """
    # Base query — always filter by user
    query = select(Task).where(Task.user_id == user_id)
    count_query = select(func.count()).select_from(Task).where(Task.user_id == user_id)

    # Full-text search
    if params.search:
        search_filter = text("task.search_vector @@ plainto_tsquery('english', :q)").bindparams(q=params.search)
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    # Priority filter
    if params.priority:
        query = query.where(Task.priority == params.priority)
        count_query = count_query.where(Task.priority == params.priority)

    # Completed filter
    if params.completed is not None:
        query = query.where(Task.completed == params.completed)
        count_query = count_query.where(Task.completed == params.completed)

    # Tag filter — join through task_tag and tag
    if params.tag:
        tag_subquery = (
            select(TaskTag.task_id)
            .join(Tag, Tag.id == TaskTag.tag_id)
            .where(Tag.name == params.tag.strip().lower(), Tag.user_id == user_id)
        )
        query = query.where(Task.id.in_(tag_subquery))
        count_query = count_query.where(col(Task.id).in_(tag_subquery))

    # Due date range filters
    if params.due_before:
        due_before_dt = datetime.fromisoformat(params.due_before)
        query = query.where(Task.due_date <= due_before_dt)
        count_query = count_query.where(Task.due_date <= due_before_dt)

    if params.due_after:
        due_after_dt = datetime.fromisoformat(params.due_after)
        query = query.where(Task.due_date >= due_after_dt)
        count_query = count_query.where(Task.due_date >= due_after_dt)

    # Get total count before pagination
    total_count = session.exec(count_query).one()

    # Sorting
    sort_field = params.sort_by or "created_at"
    sort_order = params.sort_order or "desc"
    sort_col = getattr(Task, sort_field, Task.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    page = params.page or 1
    page_size = params.page_size or 20
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    tasks = list(session.exec(query).all())
    return tasks, total_count


def get_task_by_id_and_user(session: Session, task_id: int, user_id: int) -> Optional[Task]:
    """Retrieve a specific task by ID, ensuring user ownership."""
    statement = (
        select(Task)
        .where(Task.id == task_id)
        .where(Task.user_id == user_id)
    )
    return session.exec(statement).first()


def update_task(session: Session, task: Task, params: UpdateTaskParams) -> Task:
    """Update task attributes."""
    if params.title is not None:
        task.title = params.title
    if params.description is not None:
        task.description = params.description
    if params.priority is not None:
        task.priority = params.priority
    if params.due_date is not None:
        task.due_date = datetime.fromisoformat(params.due_date)
    if params.completed is not None:
        task.completed = params.completed
    if params.recurrence_rule is not None:
        task.recurrence_rule = params.recurrence_rule
    if params.reminder_minutes is not None:
        task.reminder_minutes = params.reminder_minutes

    task.updated_at = datetime.utcnow()
    session.add(task)

    # Sync tags if provided
    if params.tags is not None:
        _sync_tags(session, task.id, task.user_id, params.tags)

    session.commit()
    session.refresh(task)
    return task


def delete_task(session: Session, task: Task) -> None:
    """Delete a task from the database."""
    session.delete(task)
    session.commit()
