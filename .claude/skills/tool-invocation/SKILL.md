---
name: tool-invocation
description: Implement agent loop for invoking MCP tools and handling responses with error strategies and parallel execution. Use when building the AI agent runner that processes tool calls from OpenAI responses.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# Tool Invocation Skill

## Purpose

Implement the agent loop for invoking MCP tools and handling responses. This skill ensures proper tool execution with multiple error handling strategies, parallel invocation support, security validation, and comprehensive logging.

## Used by

- ai-agent-designer agent
- mcp-server-specialist agent
- integration-flow-tester agent

## When to Use

- Building the AI agent runner/executor
- Implementing tool call processing from OpenAI responses
- Creating error handling strategies for tool failures
- Adding parallel tool invocation support

## Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `agent_response` | object | Yes | OpenAI response containing tool_calls |
| `tool_functions` | dict | Yes | Mapping of tool names to callable functions |
| `error_strategy` | string | Yes | Strategy: "retry", "skip", or "abort" |

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `invocation_code` | Python code | Loop for calling tools |
| `response_processing` | Python code | Code to append tool results to messages |
| `error_handling` | Python code | Exception handlers for each strategy |

## Core Implementation

```python
# File: app/agent/runner.py
# [Skill]: Tool Invocation

import json
import logging
from typing import List, Dict, Callable

logger = logging.getLogger(__name__)


def invoke_tools(
    messages: List[Dict],
    tool_calls: List[Dict],
    tool_functions: Dict[str, Callable]
) -> List[Dict]:
    """
    Invoke MCP tools and collect results.

    Args:
        messages: Current message history
        tool_calls: List of tool calls from agent
        tool_functions: Mapping of tool names to functions

    Returns:
        List of tool response messages
    """
    tool_responses = []

    for tool_call in tool_calls:
        func_name = tool_call["function"]["name"]
        tool_call_id = tool_call["id"]

        logger.info(f"Invoking tool: {func_name} (id: {tool_call_id})")

        # Parse arguments
        try:
            args = json.loads(tool_call["function"]["arguments"])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse arguments for {func_name}: {e}")
            tool_responses.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps({"error": f"Invalid arguments: {str(e)}"})
            })
            continue

        # Validate tool exists
        if func_name not in tool_functions:
            logger.error(f"Unknown tool: {func_name}")
            tool_responses.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps({"error": f"Unknown tool: {func_name}"})
            })
            continue

        # Invoke tool
        try:
            result = tool_functions[func_name](**args)
            logger.info(f"Tool {func_name} succeeded")
            tool_responses.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps(result)
            })
        except Exception as e:
            logger.error(f"Tool {func_name} failed: {e}")
            tool_responses.append({
                "tool_call_id": tool_call_id,
                "role": "tool",
                "name": func_name,
                "content": json.dumps({"error": str(e)})
            })

    return tool_responses
```

## Error Strategy Implementations

### Retry Strategy

```python
# File: app/agent/strategies.py

import time
from typing import Callable, Any

def invoke_with_retry(
    func: Callable,
    args: dict,
    max_retries: int = 3,
    delay: float = 1.0
) -> Any:
    """Invoke function with retry on failure."""
    last_error = None

    for attempt in range(max_retries):
        try:
            return func(**args)
        except Exception as e:
            last_error = e
            if attempt < max_retries - 1:
                time.sleep(delay)

    raise last_error
```

### Skip Strategy

```python
def invoke_with_skip(
    tool_calls: List[Dict],
    tool_functions: Dict[str, Callable]
) -> List[Dict]:
    """Skip failed tools, continue with others."""
    responses = []
    for tc in tool_calls:
        try:
            result = tool_functions[tc["function"]["name"]](
                **json.loads(tc["function"]["arguments"])
            )
            responses.append(format_success(tc, result))
        except Exception as e:
            responses.append(format_error(tc, str(e)))
    return responses
```

### Abort Strategy

```python
class ToolInvocationError(Exception):
    """Raised when tool invocation fails with ABORT strategy."""
    pass

def invoke_with_abort(
    tool_calls: List[Dict],
    tool_functions: Dict[str, Callable]
) -> List[Dict]:
    """Abort on first failure."""
    responses = []
    for tc in tool_calls:
        try:
            result = tool_functions[tc["function"]["name"]](
                **json.loads(tc["function"]["arguments"])
            )
            responses.append(format_success(tc, result))
        except Exception as e:
            raise ToolInvocationError(f"Tool {tc['function']['name']} failed: {e}")
    return responses
```

## Agent Loop

```python
# File: app/agent/loop.py

from openai import OpenAI

def run_agent_loop(
    client: OpenAI,
    model: str,
    messages: List[Dict],
    tool_schemas: List[Dict],
    tool_functions: Dict[str, Callable],
    max_iterations: int = 10
) -> str:
    """
    Run agent loop until completion or max iterations.

    Returns:
        Final assistant response
    """
    for _ in range(max_iterations):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_schemas,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        messages.append(msg.model_dump())

        if not msg.tool_calls:
            return msg.content or ""

        # Process tool calls
        tool_calls = [
            {"id": tc.id, "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]

        tool_responses = invoke_tools(messages, tool_calls, tool_functions)
        messages.extend(tool_responses)

    return messages[-1].get("content", "")
```

## Quality Standards

### Parallel Invocation
- Handle multiple tools in one loop iteration
- Use ThreadPoolExecutor for concurrent execution when beneficial

### JSON Safety
- Always use `json.dumps()` for results
- Catch `json.JSONDecodeError` for argument parsing

### Error Capture
- Append errors as tool responses (not exceptions for skip/retry)
- Include error details in response content

### Security
- Validate args against schema before invocation
- Sanitize user-provided values

### Logging
- Log tool name and ID on invocation
- Log success/failure outcomes

## Verification Checklist

- [ ] Tool responses include `tool_call_id`, `role`, `name`, `content`
- [ ] Results are JSON-serialized strings
- [ ] Unknown tools return error response
- [ ] Invalid JSON arguments handled gracefully
- [ ] Error strategy is configurable
- [ ] Logging captures tool invocations

## Output Format

1. **Runner implementation** in `app/agent/runner.py`
2. **Strategy implementations** in `app/agent/strategies.py`
3. **Agent loop** in `app/agent/loop.py`
