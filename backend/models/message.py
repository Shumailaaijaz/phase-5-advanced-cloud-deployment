"""Message model for chat persistence."""
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from .conversation import Conversation


class Message(SQLModel, table=True):
    """
    Represents a single message in a conversation.

    Indexes:
    - conversation_id: Fast message lookup
    - (conversation_id, created_at): Ordered message retrieval
    - user_id: User isolation queries

    Validation Rules:
    - role MUST be "user" or "assistant"
    - content MUST NOT be empty or whitespace-only
    - content max length: 10,000 characters
    """
    __tablename__ = "messages"

    id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        primary_key=True,
        max_length=36,
        description="Unique message identifier (UUID)"
    )
    conversation_id: str = Field(
        foreign_key="conversations.id",
        index=True,
        max_length=36,
        description="Parent conversation"
    )
    user_id: str = Field(
        index=True,
        max_length=255,
        description="Owner (denormalized for queries)"
    )
    role: str = Field(
        max_length=20,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        max_length=10000,
        description="Message text content"
    )
    tool_calls: Optional[str] = Field(
        default=None,
        description="JSON of tool invocations"
    )
    tool_results: Optional[str] = Field(
        default=None,
        description="JSON of tool results"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Message timestamp"
    )

    # Relationship: belongs_to Conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
