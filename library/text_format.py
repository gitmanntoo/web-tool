"""Text formatting utilities for ASCII conversion, HTML escaping, and filename sanitization."""

import html
import re

from anyascii import anyascii


def ascii_text(text: str) -> str:
    return anyascii(text)


def html_text(text: str) -> str:
    return html.escape(text)


def text_with_ascii_and_emojis(text: str) -> str:
    """
    Convert text to ASCII and emojis only (removes unicode accents/symbols).
    Preserves emoji characters while converting other unicode to ASCII equivalents.
    """
    result = []
    for char in text:
        # Check if character is an emoji or symbol (Unicode category So, No, Po, or emoji blocks)
        if ord(char) > 127:
            # Check common emoji ranges
            code = ord(char)
            # Emoji ranges: Emoticons, Transport, Miscellaneous Symbols, etc.
            if (
                0x1F300 <= code <= 0x1F9FF  # Emoji blocks (most comprehensive)
                or 0x2600 <= code <= 0x26FF  # Miscellaneous Symbols
                or 0x2700 <= code <= 0x27BF  # Dingbats
                or 0x1F000 <= code <= 0x1F02F
            ):  # Mahjong Tiles, Domino Tiles
                result.append(char)
            else:
                # Convert non-emoji unicode to ASCII
                result.append(anyascii(char))
        else:
            result.append(char)
    return "".join(result)


def text_ascii_only(text: str) -> str:
    """
    Convert text to ASCII only (converts all unicode and emojis to ASCII).
    Emojis are converted to their text equivalents (e.g., 👋 → :wave:).
    """
    return anyascii(text)


def path_safe_filename(text: str, replacement: str = "_") -> str:
    r"""
    Convert text to a path-safe filename that works on macOS, Linux, and Windows.

    Removes/replaces characters that are invalid or problematic in filenames:
    - Windows: < > : " / \ | ? *
    - Unix: / (null is also invalid but rare in text)
    - macOS: : (treated as path separator, though HFS+ uses it)
    - All: control characters, leading/trailing spaces/dots

    Args:
        text: The text to convert
        replacement: Character to use for invalid characters (default: underscore)

    Returns:
        A filename-safe string
    """
    # First convert to ASCII to remove unicode/emojis
    safe = anyascii(text)

    # Remove/replace invalid filename characters
    # Invalid on Windows: < > : " / \ | ? *
    # Invalid on Unix: / and null
    # Invalid on macOS: : (path separator in classic Mac OS)
    invalid_chars = r'[<>:"/\\|?*\x00@]'  # Added @ for safety in edge cases
    safe = re.sub(invalid_chars, replacement, safe)

    # Remove control characters
    safe = re.sub(r"[\x01-\x1f]", "", safe)

    # Remove leading/trailing spaces and dots (problematic on Windows)
    safe = safe.strip(". ")

    # Remove consecutive replacements (e.g., multiple underscores)
    safe = re.sub(f"{re.escape(replacement)}+", replacement, safe)

    # Ensure filename is not empty
    if not safe or safe == replacement:
        safe = "untitled"

    return safe
