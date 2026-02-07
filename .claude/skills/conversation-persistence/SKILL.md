---
name: conversation-persistence
description: Define database models and logic for storing conversations and messages with proper relationships, indexes, and CRUD operations. Use when implementing chat history storage for the AI chatbot.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Conversation Persistence Skill

## Purpose

Define database models and logic for storing conversations and messages. This skill ensures proper data modeling for chat history with bidirectional relationships, automatic timestamps, efficient indexing, and complete CRUD operations for history management.

## Used by

- mcp-architect agent
- chat-api-architect agent
- conversation-integrity-auditor agent

## When to Use

- Creating database models for conversation storage
- Implementing chat history persistence
- Building CRUD operations for loading/saving conversation history
- Generating Alembic migrations for conversation tables
- Ensuring proper user isolation in chat data

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model_names` | list | Yes | Model names (e.g., ["Conversation", "Message"]) |
| `fields` | object | Yes | Field definitions (user_id, content, role, etc.) |
| `relationships` | object | Yes | Relationship definitions (Conversation has many Messages) |
| `indexes` | list | Yes | Index definitions for query optimization |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `model_file` | Python code | SQLModel class definitions |
| `migration_file` | Python code | Alembic migration script |
| `crud_functions` | Python code | Functions to load/save history |

## Model Implementation

### Conversation Model

```python
# File: app/models/conversation.py
# [Skill]: Conversation Persistence

from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

class Conversation(SQLModel, table=True):
    """
    Represents a chat conversation session for a user.

    Attributes:
        id: Unique conversation identifier (UUID string)
        user_id: Owner of the conversation (indexed for fast lookup)
        title: Optional conversation title/summary
        created_at: Timestamp when conversation started
        updated_at: Timestamp of last activity
        messages: List of messages in this conversation
    """
    __tablename__ = "conversations"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Unique conversation identifier"
    )
    user_id: str = Field(
        index=True,
        nullable=False,
        description="User who owns this conversation"
    )
    title: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional conversation title"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Conversation creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Last activity timestamp"
    )

    # Relationship to messages
    messages: List["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "order_by": "Message.created_at"}
    )
```

### Message Model

```python
# File: app/models/message.py
# [Skill]: Conversation Persistence

from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime
from uuid import uuid4

class Message(SQLModel, table=True):
    """
    Represents a single message in a conversation.

    Attributes:
        id: Unique message identifier (UUID string)
        conversation_id: Parent conversation reference
        user_id: User who owns this message (for isolation queries)
        role: Message role ("user" or "assistant")
        content: Message text content
        tool_calls: JSON string of tool calls made (if any)
        tool_results: JSON string of tool results (if any)
        created_at: Message timestamp
    """
    __tablename__ = "messages"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        description="Unique message identifier"
    )
    conversation_id: str = Field(
        foreign_key="conversations.id",
        index=True,
        nullable=False,
        description="Parent conversation ID"
    )
    user_id: str = Field(
        index=True,
        nullable=False,
        description="User who owns this message"
    )
    role: str = Field(
        nullable=False,
        description="Message role: 'user' or 'assistant'"
    )
    content: str = Field(
        nullable=False,
        description="Message text content"
    )
    tool_calls: Optional[str] = Field(
        default=None,
        description="JSON string of tool calls (if assistant made tool calls)"
    )
    tool_results: Optional[str] = Field(
        default=None,
        description="JSON string of tool results (if tools were executed)"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        nullable=False,
        description="Message creation timestamp"
    )

    # Relationship back to conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
```

### Combined Models File

```python
# File: app/models/__init__.py
# [Skill]: Conversation Persistence

from .conversation import Conversation
from .message import Message
from .task import Task  # Existing task model

__all__ = ["Conversation", "Message", "Task"]
```

## Migration Implementation

### Alembic Migration Script

```python
# File: alembic/versions/002_create_conversations.py
# [Skill]: Database Migration

"""Create conversations and messages tables

Revision ID: 002_create_conversations
Revises: 001_create_tasks
Create Date: 2024-01-24

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '002_create_conversations'
down_revision = '001_create_tasks'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create conversations and messages tables with indexes."""

    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Create index for fast user lookup
    op.create_index(
        'ix_conversations_user_id',
        'conversations',
        ['user_id']
    )

    # Create composite index for user's recent conversations
    op.create_index(
        'ix_conversations_user_id_updated_at',
        'conversations',
        ['user_id', 'updated_at']
    )

    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('conversation_id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', sa.Text(), nullable=True),
        sa.Column('tool_results', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(
            ['conversation_id'],
            ['conversations.id'],
            ondelete='CASCADE'
        ),
    )

    # Create indexes for messages
    op.create_index(
        'ix_messages_conversation_id',
        'messages',
        ['conversation_id']
    )
    op.create_index(
        'ix_messages_user_id',
        'messages',
        ['user_id']
    )

    # Create composite index for loading conversation messages in order
    op.create_index(
        'ix_messages_conversation_id_created_at',
        'messages',
        ['conversation_id', 'created_at']
    )


def downgrade() -> None:
    """Remove conversations and messages tables."""

    # Drop message indexes and table
    op.drop_index('ix_messages_conversation_id_created_at', table_name='messages')
    op.drop_index('ix_messages_user_id', table_name='messages')
    op.drop_index('ix_messages_conversation_id', table_name='messages')
    op.drop_table('messages')

    # Drop conversation indexes and table
    op.drop_index('ix_conversations_user_id_updated_at', table_name='conversations')
    op.drop_index('ix_conversations_user_id', table_name='conversations')
    op.drop_table('conversations')
```

## CRUD Functions Implementation

```python
# File: app/crud/conversation.py
# [Skill]: Conversation Persistence - CRUD Operations

from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime
import logging

from app.models import Conversation, Message
from app.database import engine

logger = logging.getLogger(__name__)


# =============================================================================
# Conversation CRUD
# =============================================================================

def create_conversation(user_id: str, title: Optional[str] = None) -> Conversation:
    """
    Create a new conversation for a user.

    Args:
        user_id: Owner's user ID
        title: Optional conversation title

    Returns:
        Created Conversation object
    """
    logger.info(f"Creating conversation for user {user_id}")

    with Session(engine) as session:
        conversation = Conversation(
            user_id=user_id,
            title=title
        )
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
        return conversation


def get_conversation(conversation_id: str, user_id: str) -> Optional[Conversation]:
    """
    Get a conversation by ID, ensuring user ownership.

    Args:
        conversation_id: Conversation to retrieve
        user_id: User who must own the conversation

    Returns:
        Conversation if found and owned by user, None otherwise
    """
    with Session(engine) as session:
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        ).first()
        return conversation


def get_conversation_with_messages(
    conversation_id: str,
    user_id: str
) -> Optional[Conversation]:
    """
    Get a conversation with all its messages loaded.

    Args:
        conversation_id: Conversation to retrieve
        user_id: User who must own the conversation

    Returns:
        Conversation with messages if found, None otherwise
    """
    with Session(engine) as session:
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        ).first()

        if conversation:
            # Eagerly load messages
            _ = conversation.messages

        return conversation


def list_conversations(
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> List[Conversation]:
    """
    List conversations for a user, ordered by most recent activity.

    Args:
        user_id: User whose conversations to list
        limit: Maximum conversations to return
        offset: Number of conversations to skip

    Returns:
        List of Conversation objects
    """
    with Session(engine) as session:
        conversations = session.exec(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        ).all()
        return list(conversations)


def update_conversation_timestamp(conversation_id: str, user_id: str) -> bool:
    """
    Update the updated_at timestamp of a conversation.

    Args:
        conversation_id: Conversation to update
        user_id: User who must own the conversation

    Returns:
        True if updated, False if not found
    """
    with Session(engine) as session:
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        ).first()

        if not conversation:
            return False

        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        session.commit()
        return True


def delete_conversation(conversation_id: str, user_id: str) -> bool:
    """
    Delete a conversation and all its messages.

    Args:
        conversation_id: Conversation to delete
        user_id: User who must own the conversation

    Returns:
        True if deleted, False if not found
    """
    logger.info(f"Deleting conversation {conversation_id} for user {user_id}")

    with Session(engine) as session:
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        ).first()

        if not conversation:
            return False

        session.delete(conversation)  # Cascade deletes messages
        session.commit()
        return True


# =============================================================================
# Message CRUD
# =============================================================================

def add_message(
    conversation_id: str,
    user_id: str,
    role: str,
    content: str,
    tool_calls: Optional[str] = None,
    tool_results: Optional[str] = None
) -> Message:
    """
    Add a message to a conversation.

    Args:
        conversation_id: Conversation to add message to
        user_id: User who owns the conversation
        role: Message role ("user" or "assistant")
        content: Message content
        tool_calls: Optional JSON string of tool calls
        tool_results: Optional JSON string of tool results

    Returns:
        Created Message object

    Raises:
        ValueError: If conversation not found or not owned by user
    """
    logger.info(f"Adding {role} message to conversation {conversation_id}")

    if role not in ("user", "assistant"):
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

    with Session(engine) as session:
        # Verify conversation exists and belongs to user
        conversation = session.exec(
            select(Conversation)
            .where(Conversation.id == conversation_id)
            .where(Conversation.user_id == user_id)
        ).first()

        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found for user")

        # Create message
        message = Message(
            conversation_id=conversation_id,
            user_id=user_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results
        )
        session.add(message)

        # Update conversation timestamp
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)

        session.commit()
        session.refresh(message)
        return message


def get_messages(
    conversation_id: str,
    user_id: str,
    limit: Optional[int] = None
) -> List[Message]:
    """
    Get messages for a conversation, ordered by creation time.

    Args:
        conversation_id: Conversation to get messages for
        user_id: User who must own the conversation
        limit: Optional maximum messages to return (most recent)

    Returns:
        List of Message objects in chronological order
    """
    with Session(engine) as session:
        query = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .where(Message.user_id == user_id)
            .order_by(Message.created_at.asc())
        )

        if limit:
            # Get most recent N messages
            query = (
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .where(Message.user_id == user_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = list(session.exec(query).all())
            messages.reverse()  # Return in chronological order
        else:
            messages = list(session.exec(query).all())

        return messages


def get_message_count(conversation_id: str, user_id: str) -> int:
    """
    Get the number of messages in a conversation.

    Args:
        conversation_id: Conversation to count messages for
        user_id: User who must own the conversation

    Returns:
        Number of messages
    """
    with Session(engine) as session:
        from sqlalchemy import func
        count = session.exec(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
            .where(Message.user_id == user_id)
        ).one()
        return count


# =============================================================================
# History Reconstruction
# =============================================================================

def load_conversation_history(
    conversation_id: str,
    user_id: str
) -> List[dict]:
    """
    Load conversation history in OpenAI message format.

    Args:
        conversation_id: Conversation to load
        user_id: User who must own the conversation

    Returns:
        List of message dicts with 'role' and 'content' keys
    """
    messages = get_messages(conversation_id, user_id)

    return [
        {
            "role": msg.role,
            "content": msg.content,
            **({"tool_calls": msg.tool_calls} if msg.tool_calls else {}),
            **({"tool_results": msg.tool_results} if msg.tool_results else {})
        }
        for msg in messages
    ]


def save_conversation_turn(
    conversation_id: str,
    user_id: str,
    user_message: str,
    assistant_message: str,
    tool_calls: Optional[str] = None,
    tool_results: Optional[str] = None
) -> tuple[Message, Message]:
    """
    Save a complete conversation turn (user message + assistant response).

    Args:
        conversation_id: Conversation to save to
        user_id: User who owns the conversation
        user_message: User's message content
        assistant_message: Assistant's response content
        tool_calls: Optional JSON string of tool calls made
        tool_results: Optional JSON string of tool results

    Returns:
        Tuple of (user_message, assistant_message) Message objects
    """
    user_msg = add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="user",
        content=user_message
    )

    assistant_msg = add_message(
        conversation_id=conversation_id,
        user_id=user_id,
        role="assistant",
        content=assistant_message,
        tool_calls=tool_calls,
        tool_results=tool_results
    )

    return user_msg, assistant_msg
```

## Quality Standards

### Relationships

- Bidirectional relationships with `back_populates`
- Cascade delete for messages when conversation is deleted
- Messages ordered by `created_at` in relationship

### Timestamps

- Automatic UTC timestamps via `default_factory=datetime.utcnow`
- `updated_at` automatically updated on message addition
- Server-side defaults in migrations for consistency

### Indexes

- Primary index on `user_id` for all user-specific queries
- Index on `conversation_id` for message lookups
- Composite index on `(user_id, updated_at)` for recent conversations
- Composite index on `(conversation_id, created_at)` for message ordering

### Constraints

- Foreign key from `messages.conversation_id` to `conversations.id`
- `ON DELETE CASCADE` for automatic message cleanup
- Non-nullable constraints on required fields

### Migration Safety

- Reversible migrations with complete `downgrade()` functions
- Indexes dropped before tables in downgrade
- No data loss on rollback

## Verification Checklist

When implementing conversation persistence, verify:

- [ ] Conversation model has `user_id` indexed
- [ ] Message model has `conversation_id` and `user_id` indexed
- [ ] Bidirectional relationship with `back_populates` configured
- [ ] Cascade delete configured for messages
- [ ] All CRUD functions filter by `user_id`
- [ ] `updated_at` timestamp updated on new messages
- [ ] Migration includes all indexes
- [ ] Migration is fully reversible
- [ ] UUIDs used for primary keys (string format)
- [ ] Tool calls/results stored as JSON strings

## Output Format

When generating conversation persistence code, output:

1. **Model files** in `app/models/conversation.py` and `app/models/message.py`
2. **Migration file** in `alembic/versions/002_create_conversations.py`
3. **CRUD functions** in `app/crud/conversation.py`
4. **Updated `__init__.py`** with new model exports
