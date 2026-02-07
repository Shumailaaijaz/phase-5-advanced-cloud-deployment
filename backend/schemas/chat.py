"""Chat API request/response schemas."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime


# ==================== Request Schemas ====================

class ChatRequest(BaseModel):
    """Request schema for sending a chat message."""
    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Message content (1-10000 chars, not whitespace-only)"
    )
    conversation_id: Optional[str] = Field(
        default=None,
        description="Optional conversation ID to continue existing conversation"
    )

    @field_validator('message')
    @classmethod
    def validate_not_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace-only')
        return v


# ==================== Response Schemas ====================

class ToolCallResponse(BaseModel):
    """Response schema for a tool call."""
    tool_name: str = Field(..., description="Name of the tool called")
    status: str = Field(default="completed", description="Status: pending, completed, error")
    summary: str = Field(default="", description="Human-readable summary")


class ChatResponse(BaseModel):
    """Response schema for chat endpoint."""
    conversation_id: str = Field(..., description="Conversation UUID")
    user_message_id: str = Field(..., description="User message UUID")
    assistant_message_id: str = Field(..., description="Assistant message UUID")
    response: str = Field(..., description="Assistant's text response")
    tool_calls: Optional[List[ToolCallResponse]] = Field(default=None, description="Tool calls made")


class MessageResponse(BaseModel):
    """Response schema for a single message."""
    id: str
    role: str
    content: str
    created_at: datetime


class ConversationSummary(BaseModel):
    """Summary of a conversation for list view."""
    id: str
    title: Optional[str]
    message_count: int
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    """Response schema for listing conversations."""
    conversations: List[ConversationSummary]
    total: int


class ConversationDetailResponse(BaseModel):
    """Response schema for conversation detail with messages."""
    id: str
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]


class DeleteConversationResponse(BaseModel):
    """Response schema for conversation deletion."""
    deleted: bool
    conversation_id: str


# ==================== Error Response ====================

class ErrorResponse(BaseModel):
    """Standardized error response format."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="User-friendly error message")
