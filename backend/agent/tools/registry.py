"""Tool registry for OpenAI Agents SDK integration.

Converts MCP tool definitions to OpenAI function calling format.
"""

from dataclasses import dataclass
from typing import Dict, Any, List

from mcp.server import TOOL_DEFINITIONS as MCP_TOOL_DEFINITIONS


@dataclass
class ToolCallRecord:
    """Record of a tool call made by the agent."""
    tool_name: str
    parameters: Dict[str, Any]
    result: Dict[str, Any]
    duration_ms: int


# Convert MCP definitions to OpenAI function format
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["parameters"]
        }
    }
    for tool in MCP_TOOL_DEFINITIONS
]


def get_tools() -> List[Dict[str, Any]]:
    """Get tool definitions for agent initialization.

    Returns:
        List of tool definitions in OpenAI function calling format.
    """
    return TOOL_DEFINITIONS


def get_tool_names() -> List[str]:
    """Get list of available tool names."""
    return [tool["function"]["name"] for tool in TOOL_DEFINITIONS]
