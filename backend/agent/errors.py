"""Error handling for agent module.

Maps technical errors to user-friendly messages.
"""

from typing import Optional, Dict, Any

# Error code to friendly message mapping (English defaults)
ERROR_MESSAGES = {
    "not_found": {
        "en": "I couldn't find that task. Can you double-check the details?",
        "ur": "مجھے یہ ٹاسک نہیں ملا۔ براہِ کرم تفصیل چیک کریں۔",
        "roman_ur": "Mujhe yeh task nahi mila. Zara details check kar lein."
    },
    "validation_error": {
        "en": "Could you provide more details? I need a bit more information.",
        "ur": "کیا آپ مزید تفصیلات دے سکتے ہیں؟",
        "roman_ur": "Kya aap mazeed details de sakte hain?"
    },
    "database_error": {
        "en": "I'm having a bit of trouble right now. Please try again in a moment.",
        "ur": "ابھی کچھ مسئلہ ہے۔ براہِ کرم دوبارہ کوشش کریں۔",
        "roman_ur": "Abhi kuch masla hai. Please dobara try karein."
    },
    "timeout": {
        "en": "That took longer than expected. Let's try again.",
        "ur": "یہ توقع سے زیادہ وقت لگا۔ دوبارہ کوشش کرتے ہیں۔",
        "roman_ur": "Yeh expected se zyada time laga. Dobara try karte hain."
    },
    "unknown": {
        "en": "Something went wrong. Please try again.",
        "ur": "کچھ غلط ہو گیا۔ براہِ کرم دوبارہ کوشش کریں۔",
        "roman_ur": "Kuch galat ho gaya. Please dobara try karein."
    }
}


def to_friendly_message(
    error_code: str,
    lang: str = "en",
    context: Optional[Dict[str, Any]] = None
) -> str:
    """Convert technical error code to user-friendly message.

    Args:
        error_code: Technical error code from tool response
        lang: Language code ("en", "ur", "roman_ur")
        context: Optional context for message interpolation

    Returns:
        User-friendly error message in specified language
    """
    messages = ERROR_MESSAGES.get(error_code, ERROR_MESSAGES["unknown"])
    message = messages.get(lang, messages["en"])

    # Interpolate context if provided
    if context:
        try:
            message = message.format(**context)
        except KeyError:
            pass

    return message


def map_tool_error(tool_response: Dict[str, Any], lang: str = "en") -> str:
    """Map tool error response to friendly message.

    Args:
        tool_response: Response from MCP tool with error
        lang: Language code

    Returns:
        User-friendly error message
    """
    if not tool_response.get("error"):
        return ""

    error = tool_response["error"]
    error_code = error.get("code", "unknown")
    context = error.get("details", {})

    return to_friendly_message(error_code, lang, context)
