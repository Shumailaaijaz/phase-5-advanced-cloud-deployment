---
name: error-handling
description: Implement graceful error handling for AI responses and tool failures with user-friendly messages and recovery strategies. Use when building error handlers for the chatbot agent loop.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Error Handling Skill

## Purpose

Implement graceful error handling for AI responses and tool failures. This skill ensures user-friendly error messages, proper recovery strategies, comprehensive logging, and abuse prevention.

## Used by

- ai-agent-designer agent
- security-auditor agent
- integration-flow-tester agent

## When to Use

- Building error handlers in the agent loop
- Creating user-friendly error responses
- Implementing retry and fallback strategies
- Setting up error logging and monitoring

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `error_types` | list | Yes | Error categories to handle |
| `recovery_strategy` | string | Yes | "inform_user", "retry", or "fallback" |
| `user_messages` | dict | Yes | Friendly error texts by error type |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `handler_code` | Python code | Exception handlers for agent loop |
| `response_formats` | dict | Standardized error response structures |
| `logging_config` | Python code | Error logging setup |

## Error Types

```python
# File: app/agent/errors.py
# [Skill]: Error Handling

from enum import Enum

class ErrorType(Enum):
    TOOL_ERROR = "tool_error"           # MCP tool execution failed
    AGENT_ERROR = "agent_error"         # OpenAI API or agent loop error
    DB_ERROR = "db_error"               # Database operation failed
    VALIDATION_ERROR = "validation_error"  # Input validation failed
    AUTH_ERROR = "auth_error"           # Authentication/authorization failed
    RATE_LIMIT_ERROR = "rate_limit"     # Too many requests
    TIMEOUT_ERROR = "timeout"           # Operation timed out
```

## Core Implementation

### Error Handler

```python
# File: app/agent/error_handler.py
# [Skill]: Error Handling

import logging
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class RecoveryStrategy(Enum):
    INFORM_USER = "inform_user"   # Tell user what happened
    RETRY = "retry"               # Retry the operation
    FALLBACK = "fallback"         # Use fallback behavior


# User-friendly messages (never expose technical details)
USER_MESSAGES = {
    "tool_error": "I couldn't complete that action. Please try rephrasing your request.",
    "agent_error": "I'm having trouble processing your request. Please try again.",
    "db_error": "I couldn't save that information. Please try again in a moment.",
    "validation_error": "I didn't understand that request. Could you rephrase it?",
    "auth_error": "You don't have permission for that action.",
    "rate_limit": "You're sending requests too quickly. Please wait a moment.",
    "timeout": "That request took too long. Please try a simpler request.",
    "unknown": "Something unexpected happened. Please try again."
}

RECOVERY_SUGGESTIONS = {
    "tool_error": "Try: 'Show my tasks' or 'Add task: [description]'",
    "agent_error": "If this persists, try refreshing the page.",
    "db_error": "Your data is safe. Please retry in a few seconds.",
    "validation_error": "Example commands: 'Add task', 'List tasks', 'Complete task #1'",
    "timeout": "Try breaking your request into smaller parts."
}


def handle_error(
    error: Exception,
    error_type: str = "unknown",
    strategy: RecoveryStrategy = RecoveryStrategy.INFORM_USER,
    context: Optional[Dict] = None
) -> Dict:
    """
    Handle errors gracefully with user-friendly responses.

    Args:
        error: The caught exception
        error_type: Category of error
        strategy: How to recover
        context: Additional context for logging

    Returns:
        Standardized error response dict
    """
    # Log full error server-side (never expose to user)
    logger.error(
        f"Error [{error_type}]: {str(error)}",
        extra={
            "error_type": error_type,
            "strategy": strategy.value,
            "context": context or {}
        },
        exc_info=True
    )

    # Build user-friendly response
    user_message = USER_MESSAGES.get(error_type, USER_MESSAGES["unknown"])
    suggestion = RECOVERY_SUGGESTIONS.get(error_type, "")

    return {
        "status": "error",
        "error_type": error_type,
        "message": user_message,
        "suggestion": suggestion,
        "can_retry": strategy in (RecoveryStrategy.RETRY, RecoveryStrategy.INFORM_USER)
    }


def handle_tool_error(error: Exception, tool_name: str) -> Dict:
    """Handle MCP tool execution errors."""
    logger.error(f"Tool '{tool_name}' failed: {error}", exc_info=True)

    return {
        "status": "error",
        "message": f"I couldn't complete the {tool_name.replace('_', ' ')} action.",
        "user_friendly": USER_MESSAGES["tool_error"],
        "suggestion": RECOVERY_SUGGESTIONS["tool_error"]
    }


def handle_agent_error(error: Exception) -> Dict:
    """Handle agent loop or OpenAI API errors."""
    logger.error(f"Agent error: {error}", exc_info=True)

    return {
        "status": "error",
        "message": USER_MESSAGES["agent_error"],
        "suggestion": RECOVERY_SUGGESTIONS["agent_error"]
    }


def handle_db_error(error: Exception, operation: str) -> Dict:
    """Handle database operation errors."""
    logger.error(f"DB error during {operation}: {error}", exc_info=True)

    return {
        "status": "error",
        "message": USER_MESSAGES["db_error"],
        "suggestion": RECOVERY_SUGGESTIONS["db_error"]
    }
```

### Agent Loop Integration

```python
# File: app/agent/loop_with_errors.py
# [Skill]: Error Handling

import logging
from typing import Dict, List, Callable
from app.agent.error_handler import (
    handle_error, handle_tool_error, handle_agent_error,
    RecoveryStrategy
)

logger = logging.getLogger(__name__)


def run_agent_with_error_handling(
    messages: List[Dict],
    tool_calls: List[Dict],
    tool_functions: Dict[str, Callable],
    max_retries: int = 2
) -> Dict:
    """
    Run agent loop with comprehensive error handling.

    Args:
        messages: Conversation history
        tool_calls: Tools to invoke
        tool_functions: Available tool functions
        max_retries: Max retry attempts

    Returns:
        Response dict with results or error info
    """
    tool_results = []

    for tool_call in tool_calls:
        func_name = tool_call["function"]["name"]
        tool_call_id = tool_call["id"]

        # Validate tool exists
        if func_name not in tool_functions:
            logger.warning(f"Unknown tool requested: {func_name}")
            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(handle_error(
                    ValueError(f"Unknown tool: {func_name}"),
                    "tool_error"
                ))
            })
            continue

        # Parse arguments
        try:
            args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(handle_error(e, "validation_error"))
            })
            continue

        # Execute with retry
        result = None
        last_error = None

        for attempt in range(max_retries):
            try:
                result = tool_functions[func_name](**args)
                break
            except ValueError as e:
                # Validation errors don't retry
                last_error = e
                break
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    logger.warning(f"Retrying {func_name} (attempt {attempt + 2})")
                    continue

        if result is not None:
            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(result)
            })
        else:
            tool_results.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(handle_tool_error(last_error, func_name))
            })

    return {"tool_results": tool_results, "status": "completed"}
```

### Rate Limiting

```python
# File: app/agent/rate_limiter.py
# [Skill]: Error Handling

import time
from collections import defaultdict
from typing import Dict

# Simple in-memory rate limiter
_request_counts: Dict[str, list] = defaultdict(list)
RATE_LIMIT = 20  # requests
RATE_WINDOW = 60  # seconds


def check_rate_limit(user_id: str) -> bool:
    """
    Check if user is within rate limits.

    Args:
        user_id: User identifier

    Returns:
        True if allowed, False if rate limited
    """
    now = time.time()
    window_start = now - RATE_WINDOW

    # Clean old requests
    _request_counts[user_id] = [
        ts for ts in _request_counts[user_id]
        if ts > window_start
    ]

    # Check limit
    if len(_request_counts[user_id]) >= RATE_LIMIT:
        return False

    # Record request
    _request_counts[user_id].append(now)
    return True


def get_rate_limit_error() -> Dict:
    """Return rate limit error response."""
    return {
        "status": "error",
        "error_type": "rate_limit",
        "message": "You're sending requests too quickly.",
        "retry_after": RATE_WINDOW
    }
```

### Logging Configuration

```python
# File: app/config/logging.py
# [Skill]: Error Handling

import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "error_type"):
            log_data["error_type"] = record.error_type
        if hasattr(record, "context"):
            log_data["context"] = record.context
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def setup_logging():
    """Configure logging for error handling."""
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logging.basicConfig(
        level=logging.INFO,
        handlers=[handler]
    )

    # Set specific levels
    logging.getLogger("app.agent").setLevel(logging.DEBUG)
    logging.getLogger("app.agent.error_handler").setLevel(logging.WARNING)
```

## Quality Standards

### User-Friendly Messages
- Never expose stack traces or technical details
- Provide actionable suggestions
- Use conversational language

### Recovery Strategies
- **inform_user**: Tell user what happened, suggest alternatives
- **retry**: Automatically retry failed operations
- **fallback**: Default to text response if tools fail

### Logging
- Log full errors server-side with context
- Use structured JSON logging
- Include error type, context, and stack trace

### Rate Limiting
- Prevent abuse with request limits
- Return friendly message with retry timing
- Track per-user request counts

### Fallback Behavior
- If all tools fail, return helpful text response
- Suggest manual alternatives
- Never leave user without a response

## Verification Checklist

- [ ] No technical details in user-facing messages
- [ ] All error types have user-friendly messages
- [ ] Recovery suggestions provided for each error
- [ ] Server-side logging captures full details
- [ ] Rate limiting implemented per user
- [ ] Retry logic with max attempts
- [ ] Fallback response when tools fail

## Output Format

1. **Error handler** in `app/agent/error_handler.py`
2. **Rate limiter** in `app/agent/rate_limiter.py`
3. **Logging config** in `app/config/logging.py`
