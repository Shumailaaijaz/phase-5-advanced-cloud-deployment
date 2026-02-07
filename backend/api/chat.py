"""Chat API endpoints.

Implements:
- POST /api/{user_id}/chat - Send message
- GET /api/{user_id}/conversations - List conversations
- GET /api/{user_id}/conversations/{conversation_id} - Get conversation detail
- DELETE /api/{user_id}/conversations/{conversation_id} - Delete conversation
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session
from typing import List

from database.session import get_session
from api.deps import verify_user
from api.errors import (
    ConversationNotFoundError,
    InvalidMessageError,
    MessageTooLongError,
    ProcessingError,
)
from schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationListResponse,
    ConversationDetailResponse,
    ConversationSummary,
    MessageResponse,
    DeleteConversationResponse,
)
from crud.conversation import (
    create_conversation,
    get_conversation,
    get_conversation_with_messages,
    list_conversations,
    delete_conversation,
    update_conversation_timestamp,
    update_conversation_title,
    add_message,
    get_messages,
    get_message_count,
)
from services.agent_interface import get_agent_runner


router = APIRouter(prefix="/api/{user_id}", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    user_id: str = Depends(verify_user),
    session: Session = Depends(get_session)
) -> ChatResponse:
    """
    Send a message to the AI assistant and receive a response.

    Request Lifecycle:
    1. Verify JWT and user_id match (via verify_user dependency)
    2. Validate request body (message not empty, length check)
    3. If conversation_id provided -> load or raise ConversationNotFoundError
    4. If no conversation_id -> create new conversation
    5. Persist user message to database
    6. Load conversation history from database
    7. Build message array for agent
    8. Call agent interface (stub for now)
    9. Persist assistant response to database
    10. Update conversation.updated_at
    11. Return response with all IDs
    """
    # Validate message
    message_content = request.message.strip()
    if not message_content:
        raise InvalidMessageError()
    if len(message_content) > 10000:
        raise MessageTooLongError(len(message_content))

    # Get or create conversation
    conversation = None
    if request.conversation_id:
        conversation = get_conversation(session, request.conversation_id, user_id)
        if not conversation:
            raise ConversationNotFoundError(request.conversation_id)
    else:
        # Create new conversation with auto-generated title from first message
        title = message_content[:50] if message_content else None
        conversation = create_conversation(session, user_id, title)

    # Persist user message
    user_message = add_message(
        session=session,
        conversation_id=conversation.id,
        user_id=user_id,
        role="user",
        content=message_content
    )

    # Load conversation history for agent context
    messages = get_messages(session, conversation.id, user_id)

    # Build message array for agent
    agent_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]

    # Call agent interface
    try:
        agent = get_agent_runner()
        agent_result = agent.process(
            agent_messages,
            user_id=user_id,
            conversation_id=conversation.id,
        )
        response_text = agent_result["response"]
        tool_calls = agent_result.get("tool_calls", [])
    except Exception as e:
        raise ProcessingError(str(e))

    # Persist assistant response
    assistant_message = add_message(
        session=session,
        conversation_id=conversation.id,
        user_id=user_id,
        role="assistant",
        content=response_text
    )

    # Update conversation timestamp
    update_conversation_timestamp(session, conversation.id, user_id)

    # Auto-generate title if first message
    if not conversation.title:
        update_conversation_title(session, conversation.id, user_id, message_content)

    return ChatResponse(
        conversation_id=conversation.id,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        response=response_text,
        tool_calls=tool_calls if tool_calls else None
    )


@router.get("/conversations", response_model=ConversationListResponse)
async def get_conversations(
    user_id: str = Depends(verify_user),
    session: Session = Depends(get_session),
    limit: int = Query(default=50, ge=1, le=100, description="Max conversations to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset")
) -> ConversationListResponse:
    """
    List all conversations for the authenticated user.

    Behavior:
    1. Filter by authenticated user_id
    2. Order by updated_at DESC (most recent first)
    3. Apply pagination (limit/offset)
    4. Include message count for each conversation
    """
    conversations, total = list_conversations(session, user_id, limit, offset)

    conversation_summaries = []
    for conv in conversations:
        message_count = get_message_count(session, conv.id, user_id)
        conversation_summaries.append(
            ConversationSummary(
                id=conv.id,
                title=conv.title,
                message_count=message_count,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
        )

    return ConversationListResponse(
        conversations=conversation_summaries,
        total=total
    )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
async def get_conversation_detail(
    conversation_id: str,
    user_id: str = Depends(verify_user),
    session: Session = Depends(get_session)
) -> ConversationDetailResponse:
    """
    Get a single conversation with all messages.

    Behavior:
    1. Verify conversation belongs to authenticated user
    2. Load all messages ordered by created_at ASC
    3. Limit to 100 most recent messages
    """
    conversation = get_conversation_with_messages(session, conversation_id, user_id)
    if not conversation:
        raise ConversationNotFoundError(conversation_id)

    # Get messages (limited to 100)
    messages = get_messages(session, conversation_id, user_id, limit=100)

    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            created_at=msg.created_at
        )
        for msg in messages
    ]

    return ConversationDetailResponse(
        id=conversation.id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses
    )


@router.delete("/conversations/{conversation_id}", response_model=DeleteConversationResponse)
async def delete_conversation_endpoint(
    conversation_id: str,
    user_id: str = Depends(verify_user),
    session: Session = Depends(get_session)
) -> DeleteConversationResponse:
    """
    Delete a conversation and all its messages.

    Behavior:
    1. Verify conversation belongs to authenticated user
    2. Delete conversation (cascade deletes messages)
    3. Return confirmation
    """
    deleted = delete_conversation(session, conversation_id, user_id)
    if not deleted:
        raise ConversationNotFoundError(conversation_id)

    return DeleteConversationResponse(
        deleted=True,
        conversation_id=conversation_id
    )
