"""
Test strings for page title handling with mixed ASCII, Unicode, and Emoji.
"""

TEST_TITLES = [
    # Pure ASCII
    "Hello World",
    "Simple ASCII Title",
    
    # ASCII with numbers and punctuation
    "Title with Numbers 123 and Punctuation!",
    "Multiple...dots---dashes___underscores",
    
    # Single Unicode characters (non-ASCII)
    "Café",  # Latin with accent
    "naïve",  # French with diaeresis
    "Zürich",  # German with umlaut
    "Москва",  # Russian (Cyrillic)
    "北京",  # Chinese (Mandarin)
    "東京",  # Japanese
    "서울",  # Korean
    "मुंबई",  # Hindi
    "القاهرة",  # Arabic
    "Ελληνικά",  # Greek
    "עברית",  # Hebrew
    
    # Mixed ASCII and Unicode
    "Hello Café",
    "Welcome to Zürich",
    "Moscow - Москва",
    "Beijing 北京",
    "Tokyo 東京",
    "Seoul - 서울",
    
    # Emoji only
    "🌍",
    "😀",
    "🚀",
    "⭐",
    "❤️",
    
    # ASCII with Emoji
    "Hello 👋",
    "Welcome 🌍",
    "Star ⭐ Title",
    "Rocket 🚀 Launch",
    
    # Unicode with Emoji
    "Café ☕",
    "Tokyo 東京 🗼",
    "Moscow Москва 🏛️",
    
    # Complex mix: ASCII + Unicode + Emoji
    "Welcome to Café 🌍 ☕",
    "Hello 👋 Москва Moscow",
    "Tokyo 東京 東京 🗼 Tower",
    "I ❤️ Python 🐍",
    "Star ⭐ Moscow Москва",
    "Beijing 北京 Great Wall 🏰",
    
    # Multiple emoji in sequence
    "🌍 🌎 🌏",
    "😀 😃 😄 😁",
    "🚀 ⭐ 🌙",
    
    # Emoji with skin tone modifiers
    "Wave 👋",
    "Wave Light 👋🏻",
    "Wave Medium 👋🏽",
    "Wave Dark 👋🏿",
    
    # Zero-width characters and special unicode
    "Title with\u200bzero\u200bwidth",  # Zero-width space
    
    # Very long mixed string
    "Welcome to Café ☕ in Москва Moscow 🏛️ where we code with Python 🐍 and JavaScript 💛",
    
    # Edge cases
    "",  # Empty string
    " ",  # Single space
    "   ",  # Multiple spaces
    "\t",  # Tab
    "\n",  # Newline
    "Title\nWith\nNewlines",
    
    # Combining diacriticals
    "e̊",  # e with ring above (combining)
    "ñ",  # n with tilde (precomposed)
    "n̄",  # n with macron (combining)
]

if __name__ == "__main__":
    print("Test Title Strings")
    print("=" * 80)
    for i, title in enumerate(TEST_TITLES, 1):
        print(f"{i:2d}. [{title!r}]")
        print(f"    Display: {title}")
        print(f"    Length: {len(title)} chars, {len(title.encode('utf-8'))} bytes")
        print()
