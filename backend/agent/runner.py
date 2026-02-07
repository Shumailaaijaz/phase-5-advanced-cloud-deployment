"""Agent Runner - Main orchestrator for AI agent execution.

Handles reasoning, tool invocation, and response generation.
"""

import asyncio
import logging
import time
from typing import Callable, Dict, Any, List, Optional

from sqlmodel import Session

from agent.context import AgentContext, AgentResult, ToolCallRecord
from agent.handlers.language import detect_language, LanguageCode
from agent.handlers.response import (
    format_task_created,
    format_task_list,
    format_task_completed,
    format_task_deleted,
    format_task_updated,
    format_error,
    format_ambiguous,
    format_delete_confirmation,
    format_greeting,
    format_thanks,
)
from agent.handlers.intent import (
    match_task_by_title,
    detect_ambiguity,
    extract_task_reference,
    extract_task_id,
    is_confirmation,
    is_greeting,
    is_thanks,
)
from agent.errors import map_tool_error
from agent.prompts.system import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Guardrails
MAX_ITERATIONS = 10
TIMEOUT_SECONDS = 30


class AgentRunner:
    """Orchestrates AI agent reasoning and tool execution.

    Usage:
        runner = AgentRunner(session_factory, mcp_server)
        result = await runner.run(context, "Add task buy milk")
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        mcp_server: Any  # MCPToolServer
    ):
        """Initialize agent runner.

        Args:
            session_factory: Factory to create fresh DB sessions
            mcp_server: MCP tool server for task operations
        """
        self._session_factory = session_factory
        self._mcp_server = mcp_server
        self._pending_delete: Optional[Dict[str, Any]] = None

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
        start_time = time.time()
        tool_calls: List[ToolCallRecord] = []

        try:
            # Apply timeout
            result = await asyncio.wait_for(
                self._process_message(context, message, tool_calls),
                timeout=TIMEOUT_SECONDS
            )
            return result

        except asyncio.TimeoutError:
            logger.error(f"Agent timeout after {TIMEOUT_SECONDS}s")
            lang = detect_language(message)
            return AgentResult(
                success=False,
                response=format_error("timeout", lang=lang),
                tool_calls=tool_calls,
                error="timeout",
                language=lang
            )
        except Exception as e:
            logger.exception(f"Agent error: {e}")
            lang = detect_language(message)
            return AgentResult(
                success=False,
                response=format_error("unknown", lang=lang),
                tool_calls=tool_calls,
                error=str(e),
                language=lang
            )
        finally:
            duration = (time.time() - start_time) * 1000
            logger.info(f"Agent completed in {duration:.0f}ms with {len(tool_calls)} tool calls")

    async def _process_message(
        self,
        context: AgentContext,
        message: str,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Process user message and generate response.

        Args:
            context: Agent context
            message: User message
            tool_calls: List to append tool call records

        Returns:
            AgentResult
        """
        # Detect language
        lang = detect_language(message)
        logger.info(f"Detected language: {lang}")

        # Get user_id as integer for MCP tools
        user_id_int = int(context.user_id)

        # Handle greetings
        if is_greeting(message):
            return AgentResult(
                success=True,
                response=format_greeting(lang),
                tool_calls=[],
                language=lang
            )

        # Handle thanks
        if is_thanks(message):
            return AgentResult(
                success=True,
                response=format_thanks(lang),
                tool_calls=[],
                language=lang
            )

        # Handle pending delete confirmation
        if self._pending_delete:
            return await self._handle_delete_confirmation(
                context, message, lang, user_id_int, tool_calls
            )

        # Analyze intent and route to appropriate handler
        msg_lower = message.lower()

        # Add task intent
        if any(kw in msg_lower for kw in [
            "add", "create", "new task", "remind",
            "shamil", "banao", "naya task", "task banao", "شامل", "بناؤ",
        ]):
            return await self._handle_add_task(
                context, message, lang, user_id_int, tool_calls
            )

        # List tasks intent
        if any(kw in msg_lower for kw in [
            "show", "list", "what", "my task", "tasks",
            "dikhao", "dikha", "batao", "mere task", "فہرست", "دکھاؤ",
        ]):
            return await self._handle_list_tasks(
                context, message, lang, user_id_int, tool_calls
            )

        # Complete task intent
        if any(kw in msg_lower for kw in [
            "done", "finish", "complete", "mark",
            "mukammal", "ho gaya", "مکمل",
        ]):
            return await self._handle_complete_task(
                context, message, lang, user_id_int, tool_calls
            )

        # Delete task intent
        if any(kw in msg_lower for kw in [
            "delete", "remove", "cancel",
            "hata", "hatao", "mita", "mitao", "حذف", "ہٹاؤ",
        ]):
            return await self._handle_delete_task(
                context, message, lang, user_id_int, tool_calls
            )

        # Update task intent
        if any(kw in msg_lower for kw in [
            "update", "change", "rename", "modify", "edit",
            "badlo", "tabdeel", "تبدیل", "بدلو",
        ]):
            return await self._handle_update_task(
                context, message, lang, user_id_int, tool_calls
            )

        # Default: unrecognized intent
        fallback = {
            "en": "I can help you manage tasks. Try: add, list, complete, delete, or update a task.",
            "ur": "میں آپ کے کام میں مدد کر سکتا ہوں۔ کوشش کریں: ٹاسک شامل، فہرست، مکمل، حذف، یا اپڈیٹ کریں۔",
            "roman_ur": "Main aapke tasks manage karne mein madad kar sakta hoon. Try karein: add, list, complete, delete, ya update task.",
        }
        return AgentResult(
            success=True,
            response=fallback.get(lang, fallback["en"]),
            tool_calls=[],
            language=lang
        )

    async def _handle_add_task(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle add task intent."""
        # Extract title from message
        title = self._extract_title(message)
        if not title:
            return AgentResult(
                success=False,
                response="What would you like me to add to your tasks?" if lang == "en"
                    else "Aap kya task add karna chahte hain?" if lang == "roman_ur"
                    else "آپ کیا ٹاسک شامل کرنا چاہتے ہیں؟",
                tool_calls=[],
                language=lang
            )

        # Call add_task tool
        result = await self._call_tool(
            "add_task",
            {"user_id": context.user_id, "title": title},
            user_id_int,
            tool_calls
        )

        if result.get("success"):
            return AgentResult(
                success=True,
                response=format_task_created(result["data"], lang),
                tool_calls=tool_calls,
                language=lang
            )
        else:
            return AgentResult(
                success=False,
                response=map_tool_error(result, lang),
                tool_calls=tool_calls,
                error=result.get("error", {}).get("code"),
                language=lang
            )

    async def _handle_list_tasks(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle list tasks intent."""
        result = await self._call_tool(
            "list_tasks",
            {"user_id": context.user_id},
            user_id_int,
            tool_calls
        )

        if result.get("success"):
            return AgentResult(
                success=True,
                response=format_task_list(result["data"], lang),
                tool_calls=tool_calls,
                language=lang
            )
        else:
            return AgentResult(
                success=False,
                response=map_tool_error(result, lang),
                tool_calls=tool_calls,
                error=result.get("error", {}).get("code"),
                language=lang
            )

    async def _handle_complete_task(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle complete task intent."""
        # First list tasks to find the one to complete
        list_result = await self._call_tool(
            "list_tasks",
            {"user_id": context.user_id},
            user_id_int,
            tool_calls
        )

        if not list_result.get("success"):
            return AgentResult(
                success=False,
                response=map_tool_error(list_result, lang),
                tool_calls=tool_calls,
                language=lang
            )

        tasks = list_result["data"].get("tasks", [])

        # Try ID-based lookup first
        task_id = extract_task_id(message)
        matched = None
        matches = []
        if task_id:
            matched = next((t for t in tasks if t.get("id") == task_id), None)
            matches = [matched] if matched else []

        if not matched:
            query = extract_task_reference(message) or message
            matched, matches = match_task_by_title(query, tasks)

        if not matches:
            return AgentResult(
                success=False,
                response=format_error("not_found", lang=lang),
                tool_calls=tool_calls,
                language=lang
            )

        if detect_ambiguity(matches):
            return AgentResult(
                success=True,
                response=format_ambiguous(matches, lang),
                tool_calls=tool_calls,
                language=lang
            )

        # Complete the matched task
        result = await self._call_tool(
            "complete_task",
            {"task_id": str(matched["id"]), "user_id": context.user_id},
            user_id_int,
            tool_calls
        )

        if result.get("success"):
            return AgentResult(
                success=True,
                response=format_task_completed(matched, lang),
                tool_calls=tool_calls,
                language=lang
            )
        else:
            return AgentResult(
                success=False,
                response=map_tool_error(result, lang),
                tool_calls=tool_calls,
                language=lang
            )

    async def _handle_delete_task(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle delete task intent - requires confirmation."""
        # First list tasks
        list_result = await self._call_tool(
            "list_tasks",
            {"user_id": context.user_id},
            user_id_int,
            tool_calls
        )

        if not list_result.get("success"):
            return AgentResult(
                success=False,
                response=map_tool_error(list_result, lang),
                tool_calls=tool_calls,
                language=lang
            )

        tasks = list_result["data"].get("tasks", [])

        # Try ID-based lookup first
        task_id = extract_task_id(message)
        matched = None
        matches = []
        if task_id:
            matched = next((t for t in tasks if t.get("id") == task_id), None)
            matches = [matched] if matched else []

        if not matched:
            query = extract_task_reference(message) or message
            matched, matches = match_task_by_title(query, tasks)

        if not matches:
            return AgentResult(
                success=False,
                response=format_error("not_found", lang=lang),
                tool_calls=tool_calls,
                language=lang
            )

        if detect_ambiguity(matches):
            return AgentResult(
                success=True,
                response=format_ambiguous(matches, lang),
                tool_calls=tool_calls,
                language=lang
            )

        # Store pending delete and ask for confirmation
        self._pending_delete = {
            "task": matched,
            "user_id": context.user_id,
            "lang": lang
        }

        return AgentResult(
            success=True,
            response=format_delete_confirmation(matched["title"], lang),
            tool_calls=tool_calls,
            language=lang
        )

    async def _handle_delete_confirmation(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle delete confirmation response."""
        pending = self._pending_delete
        self._pending_delete = None  # Clear pending state

        if is_confirmation(message):
            result = await self._call_tool(
                "delete_task",
                {"task_id": str(pending["task"]["id"]), "user_id": context.user_id},
                user_id_int,
                tool_calls
            )

            if result.get("success"):
                return AgentResult(
                    success=True,
                    response=format_task_deleted(pending["task"], lang),
                    tool_calls=tool_calls,
                    language=lang
                )
            else:
                return AgentResult(
                    success=False,
                    response=map_tool_error(result, lang),
                    tool_calls=tool_calls,
                    language=lang
                )
        else:
            # Cancelled
            cancel_msg = {
                "en": "Okay, I won't delete that task.",
                "ur": "ٹھیک ہے، میں وہ ٹاسک نہیں حذف کروں گا۔",
                "roman_ur": "Theek hai, main wo task delete nahi karunga."
            }
            return AgentResult(
                success=True,
                response=cancel_msg.get(lang, cancel_msg["en"]),
                tool_calls=tool_calls,
                language=lang
            )

    async def _handle_update_task(
        self,
        context: AgentContext,
        message: str,
        lang: LanguageCode,
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> AgentResult:
        """Handle update task intent."""
        # First list tasks
        list_result = await self._call_tool(
            "list_tasks",
            {"user_id": context.user_id},
            user_id_int,
            tool_calls
        )

        if not list_result.get("success"):
            return AgentResult(
                success=False,
                response=map_tool_error(list_result, lang),
                tool_calls=tool_calls,
                language=lang
            )

        tasks = list_result["data"].get("tasks", [])

        # Try ID-based lookup first
        task_id = extract_task_id(message)
        matched = None
        matches = []
        if task_id:
            matched = next((t for t in tasks if t.get("id") == task_id), None)
            matches = [matched] if matched else []

        if not matched:
            query = extract_task_reference(message) or message
            matched, matches = match_task_by_title(query, tasks)

        if not matches:
            return AgentResult(
                success=False,
                response=format_error("not_found", lang=lang),
                tool_calls=tool_calls,
                language=lang
            )

        if detect_ambiguity(matches):
            return AgentResult(
                success=True,
                response=format_ambiguous(matches, lang),
                tool_calls=tool_calls,
                language=lang
            )

        # Extract what to update
        updates = self._extract_updates(message)
        if not updates:
            updates = {}  # No specific updates, will just touch the task

        result = await self._call_tool(
            "update_task",
            {"task_id": str(matched["id"]), "user_id": context.user_id, **updates},
            user_id_int,
            tool_calls
        )

        if result.get("success"):
            return AgentResult(
                success=True,
                response=format_task_updated(result["data"], updates, lang),
                tool_calls=tool_calls,
                language=lang
            )
        else:
            return AgentResult(
                success=False,
                response=map_tool_error(result, lang),
                tool_calls=tool_calls,
                language=lang
            )

    async def _call_tool(
        self,
        tool_name: str,
        params: Dict[str, Any],
        user_id_int: int,
        tool_calls: List[ToolCallRecord]
    ) -> Dict[str, Any]:
        """Call MCP tool and record the call.

        Args:
            tool_name: Name of tool to call
            params: Tool parameters
            user_id_int: User ID as integer
            tool_calls: List to append record to

        Returns:
            Tool response dict
        """
        start = time.time()
        logger.info(f"Calling tool: {tool_name}")

        try:
            result = self._mcp_server.call(tool_name, params, user_id_int)
        except Exception as e:
            logger.exception(f"Tool {tool_name} failed: {e}")
            result = {
                "success": False,
                "error": {"code": "tool_error", "message": str(e)}
            }

        duration_ms = int((time.time() - start) * 1000)

        tool_calls.append(ToolCallRecord(
            tool_name=tool_name,
            parameters={k: v for k, v in params.items() if k != "user_id"},
            result=result,
            duration_ms=duration_ms
        ))

        logger.info(f"Tool {tool_name} completed in {duration_ms}ms: success={result.get('success')}")
        return result

    def _extract_title(self, message: str) -> Optional[str]:
        """Extract task title from message."""
        import re

        # Remove common prefixes
        patterns = [
            r"(?:add|create|new)\s+(?:a\s+)?(?:task\s+)?(?:to\s+)?(.+)",
            r"(?:remind\s+me\s+to\s+)(.+)",
            r"(?:task\s*:\s*)(.+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # Fallback: use the whole message minus common words
        words = message.lower().split()
        skip = {"add", "create", "new", "task", "a", "to", "please", "plz"}
        title_words = [w for w in words if w not in skip]
        if title_words:
            return " ".join(title_words)

        return None

    def _extract_updates(self, message: str) -> Dict[str, Any]:
        """Extract update fields from message."""
        import re
        updates = {}

        # Priority
        if "high" in message.lower():
            updates["priority"] = "High"
        elif "low" in message.lower():
            updates["priority"] = "Low"
        elif "medium" in message.lower():
            updates["priority"] = "Medium"

        # Title rename
        rename_match = re.search(r"(?:rename|change|update)\s+(?:to|title\s+to)\s+['\"]?(.+?)['\"]?$", message, re.IGNORECASE)
        if rename_match:
            updates["title"] = rename_match.group(1).strip()

        return updates
