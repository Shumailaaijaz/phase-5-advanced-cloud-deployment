"""Language detection for response mirroring.

Detects user input language and returns appropriate language code.
"""

import re
from typing import Literal

LanguageCode = Literal["en", "ur", "roman_ur"]

# Urdu Unicode range: 0600-06FF (Arabic script used for Urdu)
URDU_PATTERN = re.compile(r'[\u0600-\u06FF]')

# Common Roman Urdu keywords (case-insensitive)
# Only include distinctly Urdu words, not English words that might appear in both
ROMAN_URDU_KEYWORDS = {
    # Greetings
    "assalam", "walaikum", "salam", "khuda", "allah",
    # Common Urdu words (not English)
    "kya", "kia", "kaise", "kaisay", "kaisa", "karo", "karein", "karna",
    "hain", "tha", "thi", "haan", "nahi", "nahin",
    "mera", "meri", "mere", "aap", "tum", "ap",
    "kar", "dein", "dijiye", "kijiye",
    "theek", "thik", "accha", "acha",
    "shukriya", "meherbani",
    "dekho", "dikhao", "batao", "bata",
    "abhi", "kal", "aaj", "parso",
    "wala", "wali", "wale",
    "mujhe", "mujhay", "humein",
    "yeh", "ye", "woh", "wo",
    "ati", "ata", "hai", "ho", "main", "tumhe", "tumhein",
    "ko", "ka", "ki", "ke", "se", "pe", "par",
    "baat", "urdu", "sakty", "sakta", "sakti",
    # Confirmations
    "ji", "bilkul", "zaroor",
}


def detect_language(message: str) -> LanguageCode:
    """Detect the language of user input.

    Detection rules:
    1. If message contains Urdu script characters -> "ur"
    2. If message contains Roman Urdu keywords -> "roman_ur"
    3. Otherwise -> "en" (default)

    Args:
        message: User's input message

    Returns:
        Language code: "en", "ur", or "roman_ur"
    """
    # Check for Urdu script (Arabic characters)
    if URDU_PATTERN.search(message):
        return "ur"

    # Check for Roman Urdu keywords
    words = set(message.lower().split())
    roman_urdu_matches = words.intersection(ROMAN_URDU_KEYWORDS)

    # If at least 2 Roman Urdu keywords found, consider it Roman Urdu
    if len(roman_urdu_matches) >= 2:
        return "roman_ur"

    # Check for single strong indicators
    strong_indicators = {"shukriya", "assalam", "walaikum", "meherbani", "karo", "karein", "dijiye"}
    if words.intersection(strong_indicators):
        return "roman_ur"

    # Default to English
    return "en"


def is_urdu_script(text: str) -> bool:
    """Check if text contains Urdu script characters."""
    return bool(URDU_PATTERN.search(text))


def is_roman_urdu(text: str) -> bool:
    """Check if text appears to be Roman Urdu."""
    return detect_language(text) == "roman_ur"
