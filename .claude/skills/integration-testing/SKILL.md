---
name: integration-testing
description: Test chatbot end-to-end including agent, tools, and database with mocked OpenAI responses. Use when writing integration tests for the AI chatbot system.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Integration Testing Skill

## Purpose

Test the chatbot end-to-end, including agent loop, MCP tools, and database operations. This skill ensures comprehensive test coverage with mocked OpenAI responses for deterministic testing.

## Used by

- integration-flow-tester agent
- conversation-integrity-auditor agent
- security-auditor agent

## When to Use

- Writing E2E tests for chat functionality
- Creating test fixtures for conversations
- Mocking OpenAI API responses
- Testing error handling and edge cases

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `test_scenarios` | list | Yes | Natural language commands to test |
| `fixtures` | list | Yes | Sample conversations and data |
| `assertions` | list | Yes | Expected tool calls and responses |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `test_file` | Python code | Pytest test scripts |
| `test_report` | JSON | Coverage and results |
| `mocks` | Python code | Mocked OpenAI responses |

## Core Implementation

### Test Configuration

```python
# File: tests/conftest.py
# [Skill]: Integration Testing

import pytest
import asyncio
from typing import Generator, AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.main import app
from app.database import get_session


# Test database
@pytest.fixture(name="engine")
def engine_fixture():
    """Create in-memory test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine


@pytest.fixture(name="session")
def session_fixture(engine) -> Generator[Session, None, None]:
    """Create test database session."""
    with Session(engine) as session:
        yield session


@pytest.fixture(name="client")
async def client_fixture(session) -> AsyncGenerator[AsyncClient, None]:
    """Create test HTTP client with DB override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


# Mock OpenAI
@pytest.fixture
def mock_openai():
    """Mock OpenAI client for deterministic tests."""
    with patch("app.agent.loop.OpenAI") as mock:
        yield mock
```

### Mock OpenAI Responses

```python
# File: tests/mocks/openai_responses.py
# [Skill]: Integration Testing

from unittest.mock import MagicMock


def create_tool_call_response(tool_name: str, arguments: dict):
    """Create mock OpenAI response with tool call."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = None
    mock_response.choices[0].message.tool_calls = [
        MagicMock(
            id=f"call_{tool_name}_123",
            function=MagicMock(
                name=tool_name,
                arguments=json.dumps(arguments)
            )
        )
    ]
    return mock_response


def create_text_response(content: str):
    """Create mock OpenAI response with text only."""
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = content
    mock_response.choices[0].message.tool_calls = None
    return mock_response


# Pre-built mock responses for common scenarios
MOCK_RESPONSES = {
    "add_task": create_tool_call_response(
        "add_task",
        {"user_id": "testuser", "title": "Buy groceries"}
    ),
    "list_tasks": create_tool_call_response(
        "list_tasks",
        {"user_id": "testuser"}
    ),
    "complete_task": create_tool_call_response(
        "complete_task",
        {"user_id": "testuser", "task_id": "task-123"}
    ),
    "greeting": create_text_response(
        "Hello! I can help you manage your tasks. Try saying 'Add task' or 'List my tasks'."
    ),
    "error_fallback": create_text_response(
        "I'm sorry, I couldn't complete that action. Please try again."
    )
}
```

### Chat Integration Tests

```python
# File: tests/integration/test_chat.py
# [Skill]: Integration Testing

import pytest
import json
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from tests.mocks.openai_responses import MOCK_RESPONSES, create_tool_call_response


@pytest.mark.asyncio
async def test_add_task_via_chat(client: AsyncClient, mock_openai):
    """Test adding a task through natural language."""
    # Setup mock to return add_task tool call, then success message
    mock_openai.return_value.chat.completions.create.side_effect = [
        MOCK_RESPONSES["add_task"],
        create_text_response("I've added 'Buy groceries' to your tasks!")
    ]

    response = await client.post(
        "/api/testuser/chat",
        json={"message": "Add a task to buy groceries"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "added" in data["response"].lower() or "created" in data["response"].lower()
    assert data["conversation_id"] is not None


@pytest.mark.asyncio
async def test_list_tasks_via_chat(client: AsyncClient, mock_openai):
    """Test listing tasks through natural language."""
    mock_openai.return_value.chat.completions.create.side_effect = [
        MOCK_RESPONSES["list_tasks"],
        create_text_response("You have 2 tasks: 1. Buy groceries 2. Clean room")
    ]

    response = await client.post(
        "/api/testuser/chat",
        json={"message": "Show me my tasks"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "tasks" in data["response"].lower()


@pytest.mark.asyncio
async def test_complete_task_via_chat(client: AsyncClient, mock_openai):
    """Test completing a task through natural language."""
    mock_openai.return_value.chat.completions.create.side_effect = [
        MOCK_RESPONSES["complete_task"],
        create_text_response("I've marked that task as complete!")
    ]

    response = await client.post(
        "/api/testuser/chat",
        json={"message": "Mark my first task as done"}
    )

    assert response.status_code == 200
    data = response.json()
    assert "complete" in data["response"].lower()


@pytest.mark.asyncio
async def test_conversation_persistence(client: AsyncClient, mock_openai):
    """Test that conversation history is persisted."""
    mock_openai.return_value.chat.completions.create.return_value = \
        MOCK_RESPONSES["greeting"]

    # First message creates conversation
    response1 = await client.post(
        "/api/testuser/chat",
        json={"message": "Hello"}
    )
    conversation_id = response1.json()["conversation_id"]

    # Second message uses same conversation
    response2 = await client.post(
        "/api/testuser/chat",
        json={
            "message": "What can you do?",
            "conversation_id": conversation_id
        }
    )

    assert response2.json()["conversation_id"] == conversation_id

    # Verify messages persisted
    history = await client.get(f"/api/testuser/conversations/{conversation_id}")
    assert len(history.json()["messages"]) >= 2


@pytest.mark.asyncio
async def test_user_isolation(client: AsyncClient, mock_openai):
    """Test that users cannot access each other's data."""
    mock_openai.return_value.chat.completions.create.return_value = \
        MOCK_RESPONSES["greeting"]

    # User A creates conversation
    response = await client.post(
        "/api/userA/chat",
        json={"message": "Hello"}
    )
    conv_id = response.json()["conversation_id"]

    # User B cannot access it
    response = await client.get(f"/api/userB/conversations/{conv_id}")
    assert response.status_code == 404
```

### Error Handling Tests

```python
# File: tests/integration/test_errors.py
# [Skill]: Integration Testing

import pytest
from unittest.mock import patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_invalid_json_body(client: AsyncClient):
    """Test handling of malformed request body."""
    response = await client.post(
        "/api/testuser/chat",
        content="not json",
        headers={"Content-Type": "application/json"}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_empty_message(client: AsyncClient):
    """Test handling of empty message."""
    response = await client.post(
        "/api/testuser/chat",
        json={"message": ""}
    )

    assert response.status_code == 400
    assert "message" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_openai_api_error(client: AsyncClient, mock_openai):
    """Test graceful handling of OpenAI API errors."""
    mock_openai.return_value.chat.completions.create.side_effect = \
        Exception("API Error")

    response = await client.post(
        "/api/testuser/chat",
        json={"message": "Hello"}
    )

    assert response.status_code == 200  # Graceful degradation
    assert "error" in response.json()["response"].lower() or \
           "try again" in response.json()["response"].lower()


@pytest.mark.asyncio
async def test_tool_execution_error(client: AsyncClient, mock_openai):
    """Test handling when tool execution fails."""
    mock_openai.return_value.chat.completions.create.return_value = \
        create_tool_call_response("add_task", {"title": ""})  # Invalid

    with patch("app.agent.tools.add_task", side_effect=ValueError("Title required")):
        response = await client.post(
            "/api/testuser/chat",
            json={"message": "Add a task"}
        )

    assert response.status_code == 200
    # Should handle error gracefully
    data = response.json()
    assert data["response"] is not None


@pytest.mark.asyncio
async def test_rate_limiting(client: AsyncClient, mock_openai):
    """Test rate limiting prevents abuse."""
    mock_openai.return_value.chat.completions.create.return_value = \
        MOCK_RESPONSES["greeting"]

    # Send many requests quickly
    responses = []
    for _ in range(25):
        r = await client.post(
            "/api/testuser/chat",
            json={"message": "Hello"}
        )
        responses.append(r)

    # Some should be rate limited
    rate_limited = [r for r in responses if r.status_code == 429]
    assert len(rate_limited) > 0
```

### Performance Tests

```python
# File: tests/integration/test_performance.py
# [Skill]: Integration Testing

import pytest
import time
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_response_time(client: AsyncClient, mock_openai):
    """Test that responses are fast enough."""
    mock_openai.return_value.chat.completions.create.return_value = \
        MOCK_RESPONSES["greeting"]

    start = time.time()
    response = await client.post(
        "/api/testuser/chat",
        json={"message": "Hello"}
    )
    elapsed = time.time() - start

    assert response.status_code == 200
    assert elapsed < 2.0, f"Response took {elapsed:.2f}s, expected < 2s"


@pytest.mark.asyncio
async def test_concurrent_requests(client: AsyncClient, mock_openai):
    """Test handling of concurrent requests."""
    import asyncio

    mock_openai.return_value.chat.completions.create.return_value = \
        MOCK_RESPONSES["greeting"]

    async def make_request(user_id: str):
        return await client.post(
            f"/api/{user_id}/chat",
            json={"message": "Hello"}
        )

    # Send 10 concurrent requests from different users
    tasks = [make_request(f"user{i}") for i in range(10)]
    responses = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r.status_code == 200 for r in responses)
```

### Test Fixtures

```python
# File: tests/fixtures/conversations.py
# [Skill]: Integration Testing

SAMPLE_CONVERSATIONS = [
    {
        "user_id": "testuser",
        "messages": [
            {"role": "user", "content": "Add a task to buy groceries"},
            {"role": "assistant", "content": "I've added 'Buy groceries' to your tasks!"},
            {"role": "user", "content": "Show my tasks"},
            {"role": "assistant", "content": "You have 1 task: Buy groceries"}
        ]
    },
    {
        "user_id": "testuser",
        "messages": [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hello! How can I help you manage your tasks today?"}
        ]
    }
]

EDGE_CASE_INPUTS = [
    "",                           # Empty
    " ",                          # Whitespace only
    "x" * 10000,                  # Very long
    "<script>alert(1)</script>",  # XSS attempt
    "'; DROP TABLE tasks; --",    # SQL injection attempt
    "\n\n\n",                     # Only newlines
    "🎉 Add task with emoji 🚀",  # Unicode
]
```

## Quality Standards

### E2E Coverage
- Test from HTTP request to database change
- Verify response format and content
- Check side effects (DB state)

### Mocking
- Mock OpenAI for deterministic tests
- Use fixtures for reproducible data
- Isolate external dependencies

### Coverage Areas
- All CRUD operations (add, list, complete, delete, update)
- Conversation persistence and retrieval
- Error handling and edge cases
- User isolation
- Rate limiting

### Performance
- Response time < 2 seconds
- Handle concurrent requests
- No memory leaks in test suite

## Verification Checklist

- [ ] All tool operations have integration tests
- [ ] OpenAI responses are mocked
- [ ] Database state is verified
- [ ] Error scenarios are covered
- [ ] User isolation is tested
- [ ] Rate limiting is tested
- [ ] Performance benchmarks pass
- [ ] Edge cases are covered

## Output Format

1. **Test config** in `tests/conftest.py`
2. **Mocks** in `tests/mocks/openai_responses.py`
3. **Integration tests** in `tests/integration/test_chat.py`
4. **Error tests** in `tests/integration/test_errors.py`
5. **Performance tests** in `tests/integration/test_performance.py`
