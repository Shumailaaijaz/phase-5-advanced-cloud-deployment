"""Response formatting utilities.

Converts tool results to natural language using language templates.
"""

from typing import Dict, Any, List, Optional
from agent.templates.confirmations import get_template, LanguageCode


def format_task_created(task_data: Dict[str, Any], lang: LanguageCode = "en") -> str:
    """Format task creation confirmation.

    Args:
        task_data: Task data from add_task tool response
        lang: Language code

    Returns:
        Formatted confirmation message
    """
    title = task_data.get("title", "task")
    return get_template("task_created", lang, title=title)


def format_task_list(
    tasks_data: Dict[str, Any],
    lang: LanguageCode = "en",
    status: str = ""
) -> str:
    """Format task list with checkboxes.

    Args:
        tasks_data: ListTasksData from list_tasks tool response
        lang: Language code
        status: Optional status filter description

    Returns:
        Formatted task list
    """
    tasks = tasks_data.get("tasks", [])

    if not tasks:
        return get_template("task_empty_list", lang)

    # Build header
    status_text = status if status else ""
    header = get_template("task_listed", lang, status=status_text)

    # Build task list with checkboxes
    lines = [header]
    for i, task in enumerate(tasks, 1):
        checkbox = "✓" if task.get("completed", False) else "☐"
        title = task.get("title", "Untitled")
        priority = task.get("priority", "")
        due = task.get("due_date", "")

        line = f"{i}. {checkbox} {title}"
        if priority:
            line += f" [{priority}]"
        if due:
            line += f" (Due: {due})"
        lines.append(line)

    return "\n".join(lines)


def format_task_completed(task_data: Dict[str, Any], lang: LanguageCode = "en") -> str:
    """Format task completion confirmation.

    Args:
        task_data: Task data from complete_task tool response
        lang: Language code

    Returns:
        Formatted confirmation message
    """
    title = task_data.get("title", "task")
    return get_template("task_completed", lang, title=title)


def format_task_deleted(task_data: Dict[str, Any], lang: LanguageCode = "en") -> str:
    """Format task deletion confirmation.

    Args:
        task_data: Task data or title from delete_task tool response
        lang: Language code

    Returns:
        Formatted confirmation message
    """
    if isinstance(task_data, str):
        title = task_data
    else:
        title = task_data.get("title", task_data.get("task_id", "task"))
    return get_template("task_deleted", lang, title=title)


def format_task_updated(
    task_data: Dict[str, Any],
    changes: Optional[Dict[str, Any]] = None,
    lang: LanguageCode = "en"
) -> str:
    """Format task update confirmation.

    Args:
        task_data: Updated task data from update_task tool response
        changes: Optional dict of what was changed
        lang: Language code

    Returns:
        Formatted confirmation message
    """
    title = task_data.get("title", "task")
    base_msg = get_template("task_updated", lang, title=title)

    # Add change details if provided
    if changes:
        change_parts = []
        if "priority" in changes:
            change_parts.append(f"priority: {changes['priority']}")
        if "due_date" in changes:
            change_parts.append(f"due: {changes['due_date']}")
        if change_parts:
            base_msg += f" ({', '.join(change_parts)})"

    return base_msg


def format_error(
    error_code: str,
    context: Optional[Dict[str, Any]] = None,
    lang: LanguageCode = "en"
) -> str:
    """Format error message.

    Args:
        error_code: Error code from tool response
        context: Optional context for message
        lang: Language code

    Returns:
        User-friendly error message
    """
    if error_code == "not_found":
        return get_template("task_not_found", lang)

    # Fall back to generic error handling
    from agent.errors import to_friendly_message
    return to_friendly_message(error_code, lang, context)


def format_ambiguous(
    matching_tasks: List[Dict[str, Any]],
    lang: LanguageCode = "en"
) -> str:
    """Format ambiguous task match message.

    Args:
        matching_tasks: List of tasks that matched
        lang: Language code

    Returns:
        Clarification request with options
    """
    header = get_template("ambiguous_request", lang)
    options = [f"- {task.get('title', 'Untitled')}" for task in matching_tasks]
    return header + "\n" + "\n".join(options)


def format_delete_confirmation(title: str, lang: LanguageCode = "en") -> str:
    """Format delete confirmation prompt.

    Args:
        title: Task title to confirm deletion
        lang: Language code

    Returns:
        Confirmation prompt
    """
    return get_template("delete_confirmation", lang, title=title)


def format_greeting(lang: LanguageCode = "en") -> str:
    """Format greeting response.

    Args:
        lang: Language code

    Returns:
        Greeting message
    """
    return get_template("greeting", lang)


def format_thanks(lang: LanguageCode = "en") -> str:
    """Format thanks response.

    Args:
        lang: Language code

    Returns:
        Thanks acknowledgment
    """
    return get_template("thanks", lang)
