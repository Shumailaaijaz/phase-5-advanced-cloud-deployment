"""OpenAI-powered Agent Runner.

Uses GPT-4 with function calling to:
1. Answer general questions naturally
2. Execute task operations through MCP tools
3. Support multilingual responses (English, Urdu, Roman Urdu)
"""

import json
import logging
from typing import Callable, Dict, Any, List, Optional

from sqlmodel import Session

from agent.context import AgentContext, AgentResult, ToolCallRecord
from mcp.server import MCPToolServer, get_tool_definitions
from core.config import settings

logger = logging.getLogger(__name__)

# System prompt for the AI assistant - Multilingual support
SYSTEM_PROMPT = """You are a helpful, friendly AI assistant that can answer ANY question and also manage tasks.

## Language Rules:
- Detect user's language (English, Urdu, Roman Urdu) and respond in the SAME language
- Urdu script (اردو) → respond in Urdu script
- Roman Urdu (like "kya haal hai") → respond in Roman Urdu
- English → respond in English

## Your Capabilities:
1. **Answer ANY Question**: Science, history, coding, math, life advice, jokes - ANYTHING!
2. **Task Management**: Use the provided tools for task operations.

## When to Use Tools:
- "add task X" / "create task" / "new task" → call add_task tool with title
- "list tasks" / "show tasks" / "my tasks" / "tasks dikhao" → call list_tasks tool
- "complete task" / "mark done" / "task done" → call complete_task tool
- "delete task" / "remove task" → call delete_task tool
- "update task" / "edit task" → call update_task tool

## When NOT to Use Tools (answer directly):
- General questions: "what is X", "who are you", "tell me about Y"
- Math: "2+2", calculations
- Jokes, stories, advice
- Greetings: "hi", "hello"

## Important:
- For task operations, you MUST use the function calling mechanism
- Do NOT write function calls as text - use the tool_calls API feature
- Always be helpful and conversational
"""


def convert_tools_to_openai_format(tools: List[Dict]) -> List[Dict]:
    """Convert MCP tool definitions to OpenAI function format."""
    openai_tools = []
    for tool in tools:
        openai_tools.append({
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool["parameters"]
            }
        })
    return openai_tools


class OpenAIAgentRunner:
    """Agent runner powered by OpenAI GPT with function calling."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        mcp_server: MCPToolServer
    ):
        """Initialize the OpenAI agent.

        Args:
            session_factory: Factory to create DB sessions
            mcp_server: MCP server for tool execution
        """
        self._session_factory = session_factory
        self._mcp_server = mcp_server
        self._client = None

    def _get_client(self):
        """Lazy initialization of OpenAI client (supports Groq as free alternative)."""
        if self._client is None:
            # Import here to avoid issues if openai not installed
            from openai import OpenAI

            # Prefer Groq (free) over OpenAI
            if settings.GROQ_API_KEY:
                logger.info("Using Groq API (free tier)...")
                self._client = OpenAI(
                    api_key=settings.GROQ_API_KEY,
                    base_url="https://api.groq.com/openai/v1"
                )
                self._use_groq = True
            elif settings.OPENAI_API_KEY:
                logger.info("Using OpenAI API...")
                self._client = OpenAI(api_key=settings.OPENAI_API_KEY)
                self._use_groq = False
            else:
                raise ValueError(
                    "No API key configured. Please set GROQ_API_KEY (free) or OPENAI_API_KEY "
                    "in Vercel Project Settings > Environment Variables."
                )
        return self._client

    def _get_model(self) -> str:
        """Get the model name from settings."""
        if getattr(self, '_use_groq', False) or settings.GROQ_API_KEY:
            return settings.GROQ_MODEL or "llama-3.3-70b-versatile"
        return settings.OPENAI_MODEL

    async def run(
        self,
        context: AgentContext,
        message: str
    ) -> AgentResult:
        """Execute agent with user message.

        Args:
            context: Request context with user_id and history
            message: User's natural language input

        Returns:
            AgentResult with response and tool call records
        """
        tool_calls_record: List[ToolCallRecord] = []

        try:
            # Build messages array
            messages = [{"role": "system", "content": SYSTEM_PROMPT}]

            # Add conversation history (last 10 messages for context)
            for msg in context.message_history[-10:]:
                role = msg.role
                content = msg.content
                if role in ["user", "assistant"] and content:
                    messages.append({"role": role, "content": content})

            # Get OpenAI tools from MCP definitions
            openai_tools = convert_tools_to_openai_format(get_tool_definitions())

            # Call OpenAI
            logger.info(f"Calling OpenAI with message: {message[:100]}...")
            client = self._get_client()
            model = self._get_model()
            logger.info(f"Using model: {model}")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                max_tokens=1024,
                temperature=0.7
            )

            assistant_message = response.choices[0].message
            logger.info(f"OpenAI response received. Tool calls: {bool(assistant_message.tool_calls)}")

            # Check if model wants to call tools
            if assistant_message.tool_calls:
                # Execute all tool calls
                tool_results = []
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)

                    # Inject user_id into params
                    tool_args["user_id"] = context.user_id

                    logger.info(f"Executing tool: {tool_name}")

                    # Call MCP tool
                    try:
                        result = self._mcp_server.call(
                            tool_name,
                            tool_args,
                            int(context.user_id)
                        )
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(result)
                        })

                        # Record the tool call
                        tool_calls_record.append(ToolCallRecord(
                            tool_name=tool_name,
                            parameters={k: v for k, v in tool_args.items() if k != "user_id"},
                            result=result,
                            duration_ms=0
                        ))
                        logger.info(f"Tool {tool_name} succeeded")
                    except Exception as e:
                        logger.exception(f"Tool {tool_name} failed: {e}")
                        tool_results.append({
                            "tool_call_id": tool_call.id,
                            "output": json.dumps({"error": str(e)})
                        })

                # Send tool results back to get final response
                # Convert assistant_message to dict properly
                assistant_dict = {
                    "role": "assistant",
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": "function",
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        }
                        for tc in assistant_message.tool_calls
                    ]
                }
                messages.append(assistant_dict)

                for tool_result in tool_results:
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_result["tool_call_id"],
                        "content": tool_result["output"]
                    })

                # Get final response
                logger.info("Getting final response after tool execution...")
                final_response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=1024,
                    temperature=0.7
                )

                response_text = final_response.choices[0].message.content or "Task completed successfully!"
            else:
                # No tool calls - direct response
                response_text = assistant_message.content or "I'm here to help! What would you like to know?"

            logger.info(f"Returning response: {response_text[:100]}...")
            return AgentResult(
                success=True,
                response=response_text,
                tool_calls=tool_calls_record,
                language="en"
            )

        except ValueError as e:
            # Configuration errors - show to user
            error_msg = str(e)
            logger.error(f"Configuration error: {error_msg}")
            return AgentResult(
                success=False,
                response=error_msg,
                tool_calls=tool_calls_record,
                error=error_msg,
                language="en"
            )
        except Exception as e:
            logger.exception(f"OpenAI agent error: {e}")
            error_msg = str(e)

            # Provide helpful error message based on error type
            if "api_key" in error_msg.lower() or "authentication" in error_msg.lower() or "invalid_api_key" in error_msg.lower():
                response_text = "OpenAI API key is invalid or not configured. Please check OPENAI_API_KEY in environment variables."
            elif "rate_limit" in error_msg.lower():
                response_text = "Too many requests. Please wait a moment and try again."
            elif "model" in error_msg.lower():
                response_text = f"Model error: {error_msg}. Please check OPENAI_MODEL setting."
            else:
                response_text = f"Error: {error_msg}"

            return AgentResult(
                success=False,
                response=response_text,
                tool_calls=tool_calls_record,
                error=error_msg,
                language="en"
            )
