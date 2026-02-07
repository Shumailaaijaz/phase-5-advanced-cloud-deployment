"""Custom exceptions and handlers for chat API.

All exceptions follow the ErrorResponse format from the API contract.
Technical details are logged server-side, friendly messages returned to users.
"""
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


# ==================== Custom Exceptions ====================

class ChatAPIException(Exception):
    """Base exception for chat API errors."""

    def __init__(
        self,
        error_code: str,
        message: str,
        status_code: int = 500,
        detail: str | None = None
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.detail = detail  # Technical detail for logging
        super().__init__(message)


class ConversationNotFoundError(ChatAPIException):
    """Raised when a conversation is not found or doesn't belong to the user."""

    def __init__(self, conversation_id: str | None = None):
        super().__init__(
            error_code="conversation_not_found",
            message="I couldn't find that conversation. Would you like to start a new one?",
            status_code=404,
            detail=f"Conversation not found: {conversation_id}" if conversation_id else None
        )


class InvalidMessageError(ChatAPIException):
    """Raised when a message is empty or whitespace-only."""

    def __init__(self):
        super().__init__(
            error_code="invalid_message",
            message="Message cannot be empty. Please type something to send.",
            status_code=400
        )


class MessageTooLongError(ChatAPIException):
    """Raised when a message exceeds the maximum length."""

    def __init__(self, length: int | None = None):
        super().__init__(
            error_code="message_too_long",
            message="Your message is too long. Please keep it under 10,000 characters.",
            status_code=400,
            detail=f"Message length: {length}" if length else None
        )


class ProcessingError(ChatAPIException):
    """Raised when agent processing fails."""

    def __init__(self, detail: str | None = None):
        super().__init__(
            error_code="processing_error",
            message="I'm having trouble processing your request. Please try again.",
            status_code=500,
            detail=detail
        )


# ==================== Exception Handlers ====================

async def chat_api_exception_handler(request: Request, exc: ChatAPIException) -> JSONResponse:
    """
    Handle ChatAPIException and return standardized error response.

    Logs technical details server-side, returns friendly message to user.
    """
    if exc.detail:
        logger.error(f"ChatAPIException: {exc.error_code} - {exc.detail}")
    else:
        logger.warning(f"ChatAPIException: {exc.error_code} - {exc.message}")

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message
        }
    )


async def conversation_not_found_handler(request: Request, exc: ConversationNotFoundError) -> JSONResponse:
    """Handle ConversationNotFoundError."""
    return await chat_api_exception_handler(request, exc)


async def invalid_message_handler(request: Request, exc: InvalidMessageError) -> JSONResponse:
    """Handle InvalidMessageError."""
    return await chat_api_exception_handler(request, exc)


async def message_too_long_handler(request: Request, exc: MessageTooLongError) -> JSONResponse:
    """Handle MessageTooLongError."""
    return await chat_api_exception_handler(request, exc)


async def processing_error_handler(request: Request, exc: ProcessingError) -> JSONResponse:
    """Handle ProcessingError."""
    return await chat_api_exception_handler(request, exc)


def register_exception_handlers(app):
    """Register all chat API exception handlers with the FastAPI app."""
    app.add_exception_handler(ConversationNotFoundError, conversation_not_found_handler)
    app.add_exception_handler(InvalidMessageError, invalid_message_handler)
    app.add_exception_handler(MessageTooLongError, message_too_long_handler)
    app.add_exception_handler(ProcessingError, processing_error_handler)
    app.add_exception_handler(ChatAPIException, chat_api_exception_handler)
