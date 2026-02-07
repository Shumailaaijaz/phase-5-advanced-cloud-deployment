from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, col, text
from typing import List, Optional
from datetime import datetime, timezone
from models.user import Task, TaskCreate, TaskUpdate
from models.tag import Tag, TaskTag
from api.deps import get_current_user
from database.session import get_session
from events.emitter import emit_event

router = APIRouter()


def _sync_tags(session: Session, task_id: int, user_id: int, tag_names: List[str]) -> None:
    """Sync tags for a task."""
    import sqlalchemy as sa
    session.exec(sa.delete(TaskTag).where(TaskTag.task_id == task_id))
    for name in tag_names:
        name = name.strip().lower()
        if not name:
            continue
        tag = session.exec(
            select(Tag).where(Tag.user_id == user_id, Tag.name == name)
        ).first()
        if tag is None:
            tag = Tag(name=name, user_id=user_id)
            session.add(tag)
            session.flush()
        session.add(TaskTag(task_id=task_id, tag_id=tag.id))


def _get_tags(session: Session, task_id: int) -> List[str]:
    """Get tag names for a task."""
    stmt = (
        select(Tag.name)
        .join(TaskTag, Tag.id == TaskTag.tag_id)
        .where(TaskTag.task_id == task_id)
        .order_by(Tag.name)
    )
    return list(session.exec(stmt).all())


def _task_to_dict(task: Task, tags: List[str] = None) -> dict:
    """Convert task to response dict with Phase V fields."""
    due_str = None
    if task.due_date is not None:
        if isinstance(task.due_date, datetime):
            due_str = task.due_date.isoformat()
        else:
            due_str = str(task.due_date)

    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "completed": task.completed,
        "priority": task.priority,
        "due_date": due_str,
        "user_id": task.user_id,
        "created_at": task.created_at.isoformat() if isinstance(task.created_at, datetime) else str(task.created_at),
        "updated_at": task.updated_at.isoformat() if isinstance(task.updated_at, datetime) else str(task.updated_at),
        "tags": tags or [],
        "recurrence_rule": getattr(task, 'recurrence_rule', None),
        "recurrence_depth": getattr(task, 'recurrence_depth', 0),
        "reminder_minutes": getattr(task, 'reminder_minutes', None),
        "reminder_sent": getattr(task, 'reminder_sent', False),
    }


@router.get("/api/{user_id}/tasks")
async def list_tasks(
    user_id: int,
    search: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    tag: Optional[str] = Query(None),
    completed: Optional[bool] = Query(None),
    due_before: Optional[str] = Query(None),
    due_after: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc"),
    page: Optional[int] = Query(1),
    page_size: Optional[int] = Query(50),
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")

    query = select(Task).where(Task.user_id == user_id)

    # Full-text search
    if search:
        search_filter = text("task.search_vector @@ plainto_tsquery('english', :q)").bindparams(q=search)
        query = query.where(search_filter)

    # Priority filter
    if priority:
        query = query.where(Task.priority == priority)

    # Completed filter
    if completed is not None:
        query = query.where(Task.completed == completed)

    # Tag filter
    if tag:
        tag_sub = (
            select(TaskTag.task_id)
            .join(Tag, Tag.id == TaskTag.tag_id)
            .where(Tag.name == tag.strip().lower(), Tag.user_id == user_id)
        )
        query = query.where(col(Task.id).in_(tag_sub))

    # Due date range
    if due_before:
        query = query.where(Task.due_date <= datetime.fromisoformat(due_before))
    if due_after:
        query = query.where(Task.due_date >= datetime.fromisoformat(due_after))

    # Sorting
    sort_col = getattr(Task, sort_by, Task.created_at)
    if sort_order == "asc":
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    # Pagination
    offset = ((page or 1) - 1) * (page_size or 50)
    query = query.offset(offset).limit(page_size or 50)

    tasks = list(session.exec(query).all())
    result = []
    for t in tasks:
        tags = _get_tags(session, t.id)
        result.append(_task_to_dict(t, tags))

    return result


@router.post("/api/{user_id}/tasks")
async def create_task(
    user_id: int,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")

    # Parse due_date string to datetime
    due_dt = None
    if task_data.due_date:
        try:
            due_dt = datetime.fromisoformat(task_data.due_date)
        except ValueError:
            due_dt = datetime.strptime(task_data.due_date, "%Y-%m-%d")

    new_task = Task(
        title=task_data.title,
        description=task_data.description or "",
        completed=False,
        priority=task_data.priority or "P3",
        due_date=due_dt,
        user_id=user_id,
        recurrence_rule=getattr(task_data, 'recurrence_rule', None),
        reminder_minutes=getattr(task_data, 'reminder_minutes', None),
    )

    session.add(new_task)
    session.flush()

    # Sync tags
    tags = []
    if task_data.tags:
        _sync_tags(session, new_task.id, user_id, task_data.tags)
        tags = task_data.tags

    session.commit()
    session.refresh(new_task)

    # Emit event AFTER commit
    emit_event("task.created", user_id, new_task.id, {
        "title": new_task.title,
        "priority": new_task.priority,
        "tags": tags,
        "recurrence_rule": new_task.recurrence_rule,
    })

    return _task_to_dict(new_task, _get_tags(session, new_task.id))


@router.delete("/api/{user_id}/tasks/{task_id}")
async def delete_task(
    user_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")

    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    title = task.title
    session.delete(task)
    session.commit()

    emit_event("task.deleted", user_id, task_id, {"title": title})
    return {"message": "Deleted"}


@router.patch("/api/{user_id}/tasks/{task_id}/toggle")
async def toggle_task(
    user_id: int,
    task_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.completed = not task.completed
    task.updated_at = datetime.utcnow()
    session.add(task)
    session.commit()
    session.refresh(task)

    event_type = "task.completed" if task.completed else "task.updated"
    emit_event(event_type, user_id, task_id, {
        "title": task.title,
        "completed": task.completed,
        "recurrence_rule": getattr(task, "recurrence_rule", None),
        "recurrence_depth": getattr(task, "recurrence_depth", 0),
    })

    return _task_to_dict(task, _get_tags(session, task.id))


@router.put("/api/{user_id}/tasks/{task_id}")
async def update_task(
    user_id: int,
    task_id: int,
    task_data: TaskUpdate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")

    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.due_date is not None:
        try:
            task.due_date = datetime.fromisoformat(task_data.due_date)
        except ValueError:
            task.due_date = datetime.strptime(task_data.due_date, "%Y-%m-%d")
    if task_data.completed is not None:
        task.completed = task_data.completed
    if hasattr(task_data, 'recurrence_rule') and task_data.recurrence_rule is not None:
        task.recurrence_rule = task_data.recurrence_rule
    if hasattr(task_data, 'reminder_minutes') and task_data.reminder_minutes is not None:
        task.reminder_minutes = task_data.reminder_minutes

    task.updated_at = datetime.utcnow()
    session.add(task)

    if task_data.tags is not None:
        _sync_tags(session, task.id, user_id, task_data.tags)

    session.commit()
    session.refresh(task)

    emit_event("task.updated", user_id, task_id, {
        "title": task.title,
        "priority": task.priority,
        "completed": task.completed,
    })

    return _task_to_dict(task, _get_tags(session, task.id))


@router.get("/api/{user_id}/tags")
async def list_tags(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List all tags for a user with task counts."""
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")

    stmt = (
        select(Tag.name, func.count(TaskTag.task_id).label("count"))
        .outerjoin(TaskTag, Tag.id == TaskTag.tag_id)
        .where(Tag.user_id == user_id)
        .group_by(Tag.name)
        .order_by(Tag.name)
    )
    results = session.exec(stmt).all()
    return [{"name": r[0], "count": r[1]} for r in results]


@router.post("/api/internal/check-reminders")
async def check_reminders(
    session: Session = Depends(get_session)
):
    """Cron-triggered endpoint: check for due reminders and emit events."""
    from events.schemas import ReminderEvent
    from events.transport import get_transport
    import asyncio

    now = datetime.now(timezone.utc)
    stmt = (
        select(Task)
        .where(
            Task.reminder_sent == False,
            Task.reminder_minutes.isnot(None),
            Task.due_date.isnot(None),
            Task.completed == False,
        )
    )
    tasks = list(session.exec(stmt).all())

    sent = 0
    transport = get_transport()
    for task in tasks:
        if isinstance(task.due_date, datetime):
            from datetime import timedelta
            remind_at = task.due_date - timedelta(minutes=task.reminder_minutes or 0)
            if now >= remind_at:
                event = ReminderEvent(
                    event_type="reminder.due",
                    user_id=task.user_id,
                    task_id=task.id,
                    task_title=task.title,
                    due_date=task.due_date.isoformat(),
                )
                await transport.publish("reminders", event.to_dict())
                task.reminder_sent = True
                session.add(task)
                sent += 1

    if sent > 0:
        session.commit()

    return {"checked": len(tasks), "sent": sent}
