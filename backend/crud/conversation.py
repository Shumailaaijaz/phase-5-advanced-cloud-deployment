"""CRUD operations for conversations and messages.

ALL functions include user_id parameter for isolation (Constitution §3.1).
"""
from sqlmodel import Session, select, func
from datetime import datetime
from typing import Optional, List
import uuid

from models.conversation import Conversation
from models.message import Message


# ==================== Conversation CRUD ====================

def create_conversation(
    session: Session,
    user_id: str,
    title: Optional[str] = None
) -> Conversation:
    """
    Create a new conversation.

    Args:
        session: Database session
        user_id: Owner user ID
        title: Optional display title

    Returns:
        Conversation: The created conversation with generated UUID
    """
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title[:255] if title else None,  # Truncate to max length
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    session.add(conversation)
    session.commit()
    session.refresh(conversation)
    return conversation


def get_conversation(
    session: Session,
    conversation_id: str,
    user_id: str
) -> Optional[Conversation]:
    """
    Get a conversation by ID, filtered by user_id for isolation.

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)

    Returns:
        Conversation | None: The conversation or None if not found
    """
    statement = select(Conversation).where(
        Conversation.id == conversation_id,
        Conversation.user_id == user_id
    )
    return session.exec(statement).first()


def get_conversation_with_messages(
    session: Session,
    conversation_id: str,
    user_id: str
) -> Optional[Conversation]:
    """
    Get a conversation with all messages loaded (eager).

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)

    Returns:
        Conversation | None: The conversation with messages or None
    """
    conversation = get_conversation(session, conversation_id, user_id)
    if conversation:
        # Eagerly load messages ordered by created_at
        _ = conversation.messages  # Access to trigger lazy load
    return conversation


def list_conversations(
    session: Session,
    user_id: str,
    limit: int = 50,
    offset: int = 0
) -> tuple[List[Conversation], int]:
    """
    List conversations for a user with message counts.

    Args:
        session: Database session
        user_id: Owner user ID (for isolation)
        limit: Max conversations to return (1-100)
        offset: Pagination offset

    Returns:
        tuple: (List[Conversation], total_count)
    """
    # Count total conversations for this user
    count_statement = select(func.count()).select_from(Conversation).where(
        Conversation.user_id == user_id
    )
    total = session.exec(count_statement).one()

    # Get conversations ordered by updated_at DESC
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .offset(offset)
        .limit(min(limit, 100))  # Cap at 100
    )
    conversations = list(session.exec(statement).all())

    return conversations, total


def delete_conversation(
    session: Session,
    conversation_id: str,
    user_id: str
) -> bool:
    """
    Delete a conversation and cascade delete all messages.

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (must verify ownership)

    Returns:
        bool: True if deleted, False if not found
    """
    conversation = get_conversation(session, conversation_id, user_id)
    if not conversation:
        return False

    session.delete(conversation)  # Cascade deletes messages
    session.commit()
    return True


def update_conversation_timestamp(
    session: Session,
    conversation_id: str,
    user_id: str
) -> None:
    """
    Update conversation's updated_at timestamp.

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)
    """
    conversation = get_conversation(session, conversation_id, user_id)
    if conversation:
        conversation.updated_at = datetime.utcnow()
        session.add(conversation)
        session.commit()


def update_conversation_title(
    session: Session,
    conversation_id: str,
    user_id: str,
    title: str
) -> Optional[Conversation]:
    """
    Update conversation title (auto-generated from first message).

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)
        title: New title (truncated to 50 chars)

    Returns:
        Conversation | None: Updated conversation or None if not found
    """
    conversation = get_conversation(session, conversation_id, user_id)
    if conversation and not conversation.title:
        conversation.title = title[:50] if title else None
        session.add(conversation)
        session.commit()
        session.refresh(conversation)
    return conversation


# ==================== Message CRUD ====================

def add_message(
    session: Session,
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
        session: Database session
        conversation_id: Parent conversation UUID
        user_id: Owner user ID (denormalized for queries)
        role: "user" or "assistant"
        content: Message text content
        tool_calls: Optional JSON of tool invocations
        tool_results: Optional JSON of tool results

    Returns:
        Message: The created message with generated UUID

    Raises:
        ValueError: If role is not "user" or "assistant"
    """
    if role not in ("user", "assistant"):
        raise ValueError(f"Invalid role: {role}. Must be 'user' or 'assistant'")

    message = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        user_id=user_id,
        role=role,
        content=content,
        tool_calls=tool_calls,
        tool_results=tool_results,
        created_at=datetime.utcnow()
    )
    session.add(message)
    session.commit()
    session.refresh(message)
    return message


def get_messages(
    session: Session,
    conversation_id: str,
    user_id: str,
    limit: int = 100
) -> List[Message]:
    """
    Get messages for a conversation ordered by created_at ASC.

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)
        limit: Max messages to return

    Returns:
        List[Message]: Messages ordered by created_at ASC
    """
    statement = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.user_id == user_id
        )
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    return list(session.exec(statement).all())


def get_message_count(
    session: Session,
    conversation_id: str,
    user_id: str
) -> int:
    """
    Get the count of messages in a conversation.

    Args:
        session: Database session
        conversation_id: Conversation UUID
        user_id: Owner user ID (for isolation)

    Returns:
        int: Number of messages
    """
    statement = select(func.count()).select_from(Message).where(
        Message.conversation_id == conversation_id,
        Message.user_id == user_id
    )
    return session.exec(statement).one()
