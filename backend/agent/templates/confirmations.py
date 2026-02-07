"""Multi-language confirmation templates.

Response templates in English, Urdu script, and Roman Urdu.
"""

from typing import Dict, Literal, Optional

LanguageCode = Literal["en", "ur", "roman_ur"]

# Task Created Templates
TASK_CREATED_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Got it! I've added the task \"{title}\" to your list.",
    "ur": "ٹھیک ہے! میں نے \"{title}\" کا ٹاسک شامل کر دیا ہے۔",
    "roman_ur": "Theek hai! Main ne \"{title}\" ka task add kar diya hai."
}

# Task Listed Templates
TASK_LISTED_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Here are your {status} tasks:",
    "ur": "یہ آپ کے {status} ٹاسکس ہیں:",
    "roman_ur": "Yeh aap ke {status} tasks hain:"
}

# Empty List Templates
TASK_EMPTY_LIST_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "You don't have any tasks yet. Would you like to add one?",
    "ur": "آپ کے پاس ابھی کوئی ٹاسک نہیں ہے۔ کیا آپ ایک شامل کرنا چاہیں گے؟",
    "roman_ur": "Aap ke paas abhi koi task nahi hai. Kya aap aik add karna chahein ge?"
}

# Task Completed Templates
TASK_COMPLETED_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Nice! The task \"{title}\" is now marked as complete.",
    "ur": "بہت خوب! \"{title}\" والا ٹاسک مکمل ہو گیا ہے۔",
    "roman_ur": "Zabardast! \"{title}\" wala task complete ho gaya hai."
}

# Task Deleted Templates
TASK_DELETED_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Done. I've deleted the task \"{title}\".",
    "ur": "ہو گیا۔ \"{title}\" والا ٹاسک حذف کر دیا گیا ہے۔",
    "roman_ur": "Ho gaya. \"{title}\" wala task delete kar diya gaya hai."
}

# Task Updated Templates
TASK_UPDATED_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Updated! The task is now called \"{title}\".",
    "ur": "اپڈیٹ ہو گیا! اب ٹاسک کا نام \"{title}\" ہے۔",
    "roman_ur": "Update ho gaya! Task ab \"{title}\" ke naam se hai."
}

# Task Not Found Templates
TASK_NOT_FOUND_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "I couldn't find that task. Can you double-check the details?",
    "ur": "مجھے یہ ٹاسک نہیں ملا۔ براہِ کرم تفصیل چیک کریں۔",
    "roman_ur": "Mujhe yeh task nahi mila. Zara details check kar lein."
}

# Ambiguous Request Templates
AMBIGUOUS_REQUEST_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "I see multiple matching tasks. Which one do you mean?",
    "ur": "اس نام کے کئی ٹاسکس ہیں۔ براہِ کرم واضح کریں۔",
    "roman_ur": "Is naam ke kai tasks hain. Bata dein kaunsa?"
}

# Delete Confirmation Templates
DELETE_CONFIRMATION_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Do you really want to delete \"{title}\"? Reply 'yes delete' to confirm.",
    "ur": "کیا آپ واقعی \"{title}\" کو حذف کرنا چاہتے ہیں؟ تصدیق کے لیے 'ہاں حذف' لکھیں۔",
    "roman_ur": "Kya aap sach mein \"{title}\" ko delete karna chahte hain? 'haan delete' likh kar confirm karein."
}

# Greeting Templates
GREETING_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "Hi! I'm here to help with your tasks. What would you like to do?",
    "ur": "السلام علیکم! میں آپ کے ٹاسکس میں مدد کے لیے حاضر ہوں۔ کیا کروں؟",
    "roman_ur": "Assalam o Alaikum! Main aap ke tasks mein madad ke liye hazir hoon. Kya karoon?"
}

# Thanks Response Templates
THANKS_TEMPLATES: Dict[LanguageCode, str] = {
    "en": "You're welcome! Let me know if you need anything else.",
    "ur": "خوش آمدید! اگر کچھ اور چاہیے تو بتائیں۔",
    "roman_ur": "Khush amdeed! Agar kuch aur chahiye to batayein."
}

# All template collections
ALL_TEMPLATES = {
    "task_created": TASK_CREATED_TEMPLATES,
    "task_listed": TASK_LISTED_TEMPLATES,
    "task_empty_list": TASK_EMPTY_LIST_TEMPLATES,
    "task_completed": TASK_COMPLETED_TEMPLATES,
    "task_deleted": TASK_DELETED_TEMPLATES,
    "task_updated": TASK_UPDATED_TEMPLATES,
    "task_not_found": TASK_NOT_FOUND_TEMPLATES,
    "ambiguous_request": AMBIGUOUS_REQUEST_TEMPLATES,
    "delete_confirmation": DELETE_CONFIRMATION_TEMPLATES,
    "greeting": GREETING_TEMPLATES,
    "thanks": THANKS_TEMPLATES,
}


def get_template(
    template_type: str,
    lang: LanguageCode = "en",
    **kwargs
) -> str:
    """Get a template string in the specified language.

    Args:
        template_type: Type of template (e.g., "task_created", "greeting")
        lang: Language code ("en", "ur", "roman_ur")
        **kwargs: Values to interpolate into the template

    Returns:
        Formatted template string in specified language
    """
    templates = ALL_TEMPLATES.get(template_type)
    if not templates:
        return ""

    template = templates.get(lang, templates.get("en", ""))

    if kwargs:
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    return template
