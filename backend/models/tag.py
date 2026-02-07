from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional


class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=50)
    user_id: int = Field(foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class TaskTag(SQLModel, table=True):
    __tablename__ = "task_tag"
    task_id: int = Field(foreign_key="task.id", primary_key=True)
    tag_id: int = Field(foreign_key="tag.id", primary_key=True)
