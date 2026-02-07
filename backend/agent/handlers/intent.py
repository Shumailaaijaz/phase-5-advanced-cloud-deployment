"""Intent detection and task matching utilities."""

from typing import List, Dict, Any, Optional, Tuple
import re


def match_task_by_title(
    query: str,
    tasks: List[Dict[str, Any]]
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """Match user's task description to actual tasks.

    Matching strategy:
    1. Exact title match (case-insensitive)
    2. Substring match (title contains query)
    3. Word overlap match

    Args:
        query: User's task description/reference
        tasks: List of user's tasks

    Returns:
        Tuple of (matched_task, all_matching_tasks)
        - If exactly one match: (task, [task])
        - If multiple matches: (None, [matching_tasks])
        - If no matches: (None, [])
    """
    if not tasks or not query:
        return None, []

    query_lower = query.lower().strip()
    query_words = set(query_lower.split())

    matches = []
    exact_match = None

    for task in tasks:
        title = task.get("title", "").lower()

        # Exact match
        if title == query_lower:
            exact_match = task
            matches = [task]
            break

        # Substring match
        if query_lower in title or title in query_lower:
            matches.append(task)
            continue

        # Word overlap match (at least 50% of query words in title)
        title_words = set(title.split())
        overlap = query_words.intersection(title_words)
        if len(overlap) >= len(query_words) * 0.5 and len(overlap) >= 1:
            matches.append(task)

    if exact_match:
        return exact_match, [exact_match]

    if len(matches) == 1:
        return matches[0], matches

    return None, matches


def detect_ambiguity(matches: List[Dict[str, Any]]) -> bool:
    """Check if task matches are ambiguous.

    Args:
        matches: List of matching tasks

    Returns:
        True if ambiguous (more than one match)
    """
    return len(matches) > 1


def extract_task_id(message: str) -> Optional[int]:
    """Extract numeric task ID from message.

    Matches patterns like:
    - "task id 5"
    - "task #5"
    - "task no 5"
    - "id 5"

    Returns:
        Integer task ID or None
    """
    patterns = [
        r"(?:task\s+)?(?:id|#|no\.?|number)\s*(\d+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return int(match.group(1))
    return None


def extract_task_reference(message: str) -> Optional[str]:
    """Extract task reference from user message.

    Looks for patterns like:
    - "the X task"
    - "task X"
    - "X task"
    - "my X"

    Args:
        message: User's message

    Returns:
        Extracted task reference or None
    """
    patterns = [
        r"(?:the|my)\s+['\"]?(.+?)['\"]?\s+task",
        r"task\s+['\"]?(.+?)['\"]?(?:\s|$)",
        r"['\"](.+?)['\"]",
        r"(?:mark|complete|delete|update|remove)\s+['\"]?(.+?)['\"]?(?:\s+as|\s+task|$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()

    return None


def is_confirmation(message: str) -> bool:
    """Check if message is a confirmation for destructive action.

    Args:
        message: User's message

    Returns:
        True if message confirms action
    """
    confirmations = {
        # English
        "yes", "yes delete", "confirm", "do it", "go ahead", "ok", "okay",
        # Roman Urdu
        "haan", "haan delete", "ji", "ji haan", "theek hai", "kar do",
        # Urdu script
        "ہاں", "جی ہاں", "ٹھیک ہے",
    }
    return message.lower().strip() in confirmations


def is_cancellation(message: str) -> bool:
    """Check if message cancels a pending action.

    Args:
        message: User's message

    Returns:
        True if message cancels action
    """
    cancellations = {
        # English
        "no", "cancel", "stop", "nevermind", "never mind", "nope",
        # Roman Urdu
        "nahi", "nahi nahi", "ruko", "mat karo", "rehne do",
        # Urdu script
        "نہیں", "رکو", "مت کرو",
    }
    return message.lower().strip() in cancellations


def is_greeting(message: str) -> bool:
    """Check if message is a greeting.

    Args:
        message: User's message

    Returns:
        True if message is a greeting
    """
    greetings = {
        # English
        "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
        # Roman Urdu
        "assalam", "assalam o alaikum", "salam", "aoa",
        # Urdu script
        "السلام علیکم", "سلام",
    }
    msg_lower = message.lower().strip()
    return msg_lower in greetings or any(g in msg_lower for g in greetings)


def is_thanks(message: str) -> bool:
    """Check if message is a thank you.

    Args:
        message: User's message

    Returns:
        True if message is thanks
    """
    thanks = {
        # English
        "thanks", "thank you", "thank u", "thx", "ty",
        # Roman Urdu
        "shukriya", "shukria", "meherbani",
        # Urdu script
        "شکریہ", "مہربانی",
    }
    msg_lower = message.lower().strip()
    return msg_lower in thanks or any(t in msg_lower for t in thanks)
