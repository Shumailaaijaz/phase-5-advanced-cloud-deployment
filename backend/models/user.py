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
# 2. Task Table
class Task(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(min_length=1)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    priority: str = Field(default="Medium")
    user_id: int = Field(foreign_key="user.id")
    
    # SAHI LINE: back_populates mein "tasks" aayega kyunki User model mein variable ka naam "tasks" hai
    user: Optional["User"] = Relationship(back_populates="tasks") 
    
    due_date: Optional[str] = Field(default=None)
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
    priority: str = "Medium"  # Frontend se aane wali value pakadne ke liye
    due_date: Optional[str] = None

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

class TaskUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = None
    due_date: Optional[str] = None