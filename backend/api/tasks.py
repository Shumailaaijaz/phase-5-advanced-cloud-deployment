from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from typing import List
from models.user import Task, TaskCreate
from api.deps import get_current_user
from database.session import get_session

router = APIRouter()

@router.get("/api/{user_id}/tasks", response_model=List[Task])
async def list_tasks(
    user_id: int,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    statement = select(Task).where(Task.user_id == user_id)
    return session.exec(statement).all()

@router.post("/api/{user_id}/tasks", response_model=Task)
async def create_task(
    user_id: int,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Security check
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="User ID mismatch")
    
    # Naya task object banana (Directly assigning values)
    new_task = Task(
        title=task_data.title,
        description=task_data.description or "",
        completed=False,
        priority=task_data.priority, # Schema se value uthayega
        due_date=task_data.due_date,
        user_id=user_id
    )
    
    session.add(new_task)
    session.commit()
    session.refresh(new_task)
    return new_task

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
        
    session.delete(task)
    session.commit()
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
    session.add(task)
    session.commit()
    session.refresh(task)
    return task

@router.put("/api/{user_id}/tasks/{task_id}", response_model=Task)
async def update_task(
    user_id: int,
    task_id: int,
    task_data: TaskCreate,
    current_user: dict = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if int(current_user["user_id"]) != int(user_id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    task = session.get(Task, task_id)
    if not task or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task.title = task_data.title
    task.priority = task_data.priority
    task.due_date = task_data.due_date
    if task_data.description is not None:
        task.description = task_data.description
    
    session.add(task)
    session.commit()
    session.refresh(task)
    return task