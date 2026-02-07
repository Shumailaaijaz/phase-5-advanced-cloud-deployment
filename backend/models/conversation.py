"""Conversation model for chat persistence."""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .message import Message


class Conversation(SQLModel, table=True):
    """
    Represents a chat session between a user and the AI assistant.

    Indexes:
    - user_id: Fast lookup by user
    - (user_id, updated_at): Sorted list of user's conversations
    """
    __tablename__ = "conversations"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
        description="Unique conversation identifier (UUID)"
    )
    user_id: str = Field(
        index=True,
        max_length=255,
        description="Owner of conversation (user isolation)"
    )
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Display title (auto-generated or null)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Conversation start time"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Last activity time"
    )

    # Relationship: has_many Messages with cascade delete
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
