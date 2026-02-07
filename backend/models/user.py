from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List

# 1. User Table
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = Field(default=None)
    hashed_password: str = Field()
    created_at: datetime = Field(default_factory=datetime.utcnow)
    tasks: List["Task"] = Relationship(back_populates="user")

# 2. Task Table
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="P3", max_length=2)
    user_id: int = Field(foreign_key="user.id")

    user: Optional["User"] = Relationship(back_populates="tasks")

    # Phase III field — now TIMESTAMPTZ after migration 007
    due_date: Optional[datetime] = Field(default=None)

    # Phase V: Recurrence (migration 008)
    recurrence_rule: Optional[str] = Field(default=None, max_length=100)
    recurrence_parent_id: Optional[int] = Field(default=None, foreign_key="task.id")
    recurrence_depth: int = Field(default=0)

    # Phase V: Reminders (migration 009)
    reminder_minutes: Optional[int] = Field(default=None)
    reminder_sent: bool = Field(default=False)

# 3. Schemas
class UserCreate(SQLModel):
    email: str
    password: str
    full_name: Optional[str] = None

class UserRead(SQLModel):
    id: int
    email: str

class TaskCreate(SQLModel):
    title: str
    description: Optional[str] = None
    completed: bool = False
    priority: str = "P3"
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes: Optional[int] = None

class TaskRead(SQLModel):
    id: int
    title: str
    description: Optional[str]
    completed: bool
    priority: str
    due_date: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: datetime
    recurrence_rule: Optional[str] = None
    recurrence_depth: int = 0
    reminder_minutes: Optional[int] = None
    reminder_sent: bool = False
    tags: Optional[List[str]] = None

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None
    tags: Optional[List[str]] = None
    recurrence_rule: Optional[str] = None
    reminder_minutes: Optional[int] = None
