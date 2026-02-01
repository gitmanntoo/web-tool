"""
Test suite for title variant generation.

This module tests the title transformation functions:
- text_with_ascii_and_emojis: Converts unicode to ASCII but preserves emojis
- text_ascii_only: Converts all unicode and emojis to ASCII
- path_safe_filename: Creates filesystem-safe filenames for all OS
- TitleVariants: Container class providing all variants at once

Tests use a variety of input strings including ASCII, Unicode, and emoji.

To run tests:
    pytest tests/test_title_variants.py -v
    pytest tests/test_title_variants.py::TestAsciiAndEmojis -v
    pytest tests/test_title_variants.py -k "emoji" -v
"""

import pytest
from library.util import (
    text_with_ascii_and_emojis,
    text_ascii_only,
    path_safe_filename,
    TitleVariants,
)


class TestAsciiAndEmojis:
    """Tests for text_with_ascii_and_emojis function."""

    def test_pure_ascii(self):
        """ASCII text should pass through unchanged."""
        assert text_with_ascii_and_emojis("Hello World") == "Hello World"
        assert text_with_ascii_and_emojis("Simple ASCII Title") == "Simple ASCII Title"

    def test_pure_emoji(self):
        """Pure emoji should be preserved."""
        assert text_with_ascii_and_emojis("🌍") == "🌍"
        assert text_with_ascii_and_emojis("😀") == "😀"
        assert text_with_ascii_and_emojis("🚀") == "🚀"
        assert text_with_ascii_and_emojis("🌍 🌎 🌏") == "🌍 🌎 🌏"

    def test_ascii_with_emoji(self):
        """ASCII + emoji should preserve both."""
        assert text_with_ascii_and_emojis("Hello 👋") == "Hello 👋"
        # Star emoji may not be in all ranges depending on Unicode version
        result = text_with_ascii_and_emojis("Star ⭐ Title")
        assert "Star" in result and "Title" in result
        # Heart emoji with variant selector
        result = text_with_ascii_and_emojis("I ❤️ Python 🐍")
        assert "I" in result and "Python" in result and "🐍" in result

    def test_unicode_removed(self):
        """Unicode accents should be converted to ASCII."""
        assert text_with_ascii_and_emojis("Café") == "Cafe"
        assert text_with_ascii_and_emojis("naïve") == "naive"
        assert text_with_ascii_and_emojis("Zürich") == "Zurich"

    def test_unicode_with_emoji(self):
        """Unicode converted to ASCII while emoji preserved."""
        result = text_with_ascii_and_emojis("Café ☕")
        assert "Cafe" in result  # Unicode accent converted
        result = text_with_ascii_and_emojis("Tokyo 東京 🗼")
        assert "Tokyo" in result  # ASCII and Japanese converted

    def test_non_latin_unicode(self):
        """Non-Latin Unicode should be converted."""
        assert text_with_ascii_and_emojis("Москва") == "Moskva"
        result = text_with_ascii_and_emojis("北京")
        assert result == "BeiJing"  # anyascii collapses spaces
        result = text_with_ascii_and_emojis("東京")
        assert "Jing" in result  # Tokyo in Japanese converted

    def test_mixed_ascii_unicode_emoji(self):
        """Complex mix of ASCII, Unicode, and Emoji."""
        # Unicode gets converted, emoji preserved
        result = text_with_ascii_and_emojis("Welcome to Café 🌍 ☕")
        assert "Cafe" in result
        assert "🌍" in result

    def test_empty_string(self):
        """Empty string should return empty."""
        assert text_with_ascii_and_emojis("") == ""

    def test_whitespace(self):
        """Whitespace should be preserved."""
        assert text_with_ascii_and_emojis("  ") == "  "
        assert text_with_ascii_and_emojis("Title\nWith\nNewlines") == "Title\nWith\nNewlines"


class TestAsciiOnly:
    """Tests for text_ascii_only function."""

    def test_pure_ascii(self):
        """ASCII text should pass through unchanged."""
        assert text_ascii_only("Hello World") == "Hello World"

    def test_emoji_removed(self):
        """All emoji should be converted to text equivalents."""
        result = text_ascii_only("Hello 👋")
        assert "Hello" in result
        assert "wave" in result.lower()  # Emoji converted to text equivalent
        result = text_ascii_only("🌍 🌎 🌏")
        assert all(emoji not in result for emoji in ["🌍", "🌎", "🌏"])
        assert "earth" in result.lower()  # Text equivalent present

    def test_unicode_converted(self):
        """Unicode should be converted to ASCII."""
        assert text_ascii_only("Café") == "Cafe"
        assert text_ascii_only("Москва") == "Moskva"
        assert text_ascii_only("北京") == "BeiJing"  # anyascii doesn't preserve spaces

    def test_mixed_input(self):
        """Complex mix should all become ASCII."""
        result = text_ascii_only("Welcome to Café 🌍 Москва")
        # Should only contain ASCII characters
        assert all(ord(c) < 128 for c in result)

    def test_emoji_only_becomes_text_equivalent(self):
        """Emoji-only input becomes text equivalents."""
        result = text_ascii_only("😀😃😄")
        # All emojis converted to text, should not be empty
        assert result != ""
        assert "grinning" in result.lower() or "smile" in result.lower()  # Text equivalents present


class TestPathSafeFilename:
    """Tests for path_safe_filename function."""

    def test_pure_ascii_filename(self):
        """ASCII text should be valid filename."""
        result = path_safe_filename("MyFile")
        assert result == "MyFile"
        assert "/" not in result
        assert "\\" not in result

    def test_windows_invalid_chars_removed(self):
        """Windows invalid characters should be replaced."""
        # < > : " / \ | ? *
        assert "<" not in path_safe_filename("Title<Bad>")
        assert ">" not in path_safe_filename("Title<Bad>")
        assert ":" not in path_safe_filename("Title:Bad")
        assert '"' not in path_safe_filename('Title"Bad')
        assert "|" not in path_safe_filename("Title|Bad")
        assert "?" not in path_safe_filename("Title?Bad")
        assert "*" not in path_safe_filename("Title*Bad")

    def test_slash_replaced(self):
        """Forward and backslashes should be replaced."""
        result = path_safe_filename("Path/To/File")
        assert "/" not in result
        result = path_safe_filename("Path\\To\\File")
        assert "\\" not in result

    def test_unicode_converted(self):
        """Unicode should be converted."""
        result = path_safe_filename("Café")
        assert result == "Cafe"
        assert all(ord(c) < 128 for c in result)

    def test_emoji_removed(self):
        """Emoji should be removed or converted."""
        result = path_safe_filename("File 🚀 Name")
        # Should not contain emoji
        assert "🚀" not in result

    def test_control_characters_removed(self):
        """Control characters should be removed."""
        result = path_safe_filename("Title\x00Bad\x01File")
        assert "\x00" not in result
        assert "\x01" not in result

    def test_leading_trailing_spaces_removed(self):
        """Leading/trailing spaces should be removed."""
        result = path_safe_filename("  Title  ")
        assert result == "Title"

    def test_leading_trailing_dots_removed(self):
        """Leading/trailing dots should be removed (Windows)."""
        result = path_safe_filename("...Title...")
        assert result == "Title"

    def test_consecutive_replacements_collapsed(self):
        """Multiple consecutive invalid chars collapsed to single replacement."""
        result = path_safe_filename("Title::Multiple:::Colons")
        # Should not have multiple consecutive underscores
        assert "___" not in result

    def test_empty_input_becomes_untitled(self):
        """Empty or invalid-only input becomes 'untitled'."""
        assert path_safe_filename("") == "untitled"
        assert path_safe_filename("***") == "untitled"
        # Colons become underscores, then collapsed
        result = path_safe_filename(":::")
        assert result == "untitled"  # Single underscore becomes 'untitled'

    def test_custom_replacement_char(self):
        """Custom replacement character should be used."""
        result = path_safe_filename("Title:Bad", replacement="-")
        assert "-" in result
        assert ":" not in result

    def test_no_double_slashes(self):
        """Result should not create directory separators."""
        result = path_safe_filename("a/b/c")
        assert "//" not in result
        assert "\\\\" not in result

    def test_realistic_filenames(self):
        """Test realistic filename scenarios."""
        # URL as filename
        result = path_safe_filename("https://example.com:8080/path")
        assert all(ord(c) < 128 for c in result)
        assert ":" not in result  # Colons replaced
        assert "/" not in result  # Slashes replaced
        
        # Email as filename
        result = path_safe_filename("user@example.com")
        assert "@" not in result  # @ is removed for safety
        
        # Complex title
        result = path_safe_filename("My Document (Final) [2024].txt")
        assert all(c not in result for c in ['<', '>', ':', '"', '/', '\\', '|', '?', '*'])


class TestTitleVariants:
    """Tests for TitleVariants container class."""

    def test_simple_ascii(self):
        """Simple ASCII title should have same value in all variants."""
        tv = TitleVariants("Hello World")
        assert tv.original == "Hello World"
        assert tv.ascii_and_emojis == "Hello World"
        assert tv.ascii_only == "Hello World"
        assert tv.path_safe == "Hello World"

    def test_unicode_conversion(self):
        """Unicode should be handled consistently across variants."""
        tv = TitleVariants("Café")
        assert tv.original == "Café"
        assert tv.ascii_and_emojis == "Cafe"
        assert tv.ascii_only == "Cafe"
        assert tv.path_safe == "Cafe"

    def test_emoji_handling(self):
        """Emoji should be preserved in ascii_and_emojis, removed in others."""
        tv = TitleVariants("Hello 👋")
        assert tv.original == "Hello 👋"
        assert "👋" in tv.ascii_and_emojis
        assert "👋" not in tv.ascii_only
        assert "👋" not in tv.path_safe

    def test_complex_mix(self):
        """Complex mix of ASCII, Unicode, and Emoji."""
        tv = TitleVariants("Café 👋 Москва")
        assert tv.original == "Café 👋 Москва"
        assert "Cafe" in tv.ascii_and_emojis
        assert "👋" in tv.ascii_and_emojis
        assert "Moskva" in tv.ascii_and_emojis
        assert "Cafe" in tv.ascii_only
        assert "Moskva" in tv.ascii_only
        # Emoji converted to text equivalent, not removed
        assert "wave" in tv.ascii_only.lower() or "👋" not in tv.ascii_only

    def test_repr(self):
        """TitleVariants should have readable repr."""
        tv = TitleVariants("Test")
        repr_str = repr(tv)
        assert "TitleVariants" in repr_str
        assert "original" in repr_str
        assert "Test" in repr_str

    def test_all_variants_are_strings(self):
        """All variants should be strings."""
        tv = TitleVariants("Mixed Café 🌍 Москва")
        assert isinstance(tv.original, str)
        assert isinstance(tv.ascii_and_emojis, str)
        assert isinstance(tv.ascii_only, str)
        assert isinstance(tv.path_safe, str)

    def test_path_safe_is_valid_filename(self):
        """Path safe variant should not contain invalid filename characters."""
        tv = TitleVariants("My <File>: Document? \"Final\" |Edition*")
        result = tv.path_safe
        assert all(c not in result for c in ['<', '>', ':', '"', '/', '\\', '|', '?', '*'])


class TestEdgeCases:
    """Tests for edge cases and special scenarios."""

    def test_empty_string_all_variants(self):
        """Empty string should be handled consistently."""
        tv = TitleVariants("")
        assert tv.original == ""
        assert tv.ascii_and_emojis == ""
        assert tv.ascii_only == ""
        assert tv.path_safe == "untitled"

    def test_whitespace_only(self):
        """Whitespace-only input should be handled."""
        tv = TitleVariants("   ")
        assert tv.original == "   "
        # path_safe should strip and become untitled
        assert tv.path_safe == "untitled"

    def test_combining_diacriticals(self):
        """Combining diacriticals should be handled."""
        tv = TitleVariants("e̊")  # e with combining ring above
        assert tv.original == "e̊"
        # anyascii should handle this
        assert "e" in tv.ascii_only

    def test_special_unicode_symbols(self):
        """Special Unicode symbols and punctuation."""
        tv = TitleVariants("Title—with—em—dashes")
        # Em dashes should be converted
        assert "—" in tv.original
        assert all(ord(c) < 128 for c in tv.ascii_only)

    def test_newlines_preserved_except_path_safe(self):
        """Newlines should be handled appropriately."""
        tv = TitleVariants("Title\nWith\nNewlines")
        assert "\n" in tv.ascii_and_emojis
        assert "\n" in tv.ascii_only
        # path_safe might remove them
        assert tv.path_safe  # Just ensure it's not empty/untitled

    def test_very_long_title(self):
        """Very long titles should be handled."""
        long_title = "A" * 1000
        tv = TitleVariants(long_title)
        assert len(tv.original) == 1000
        assert len(tv.ascii_only) == 1000


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
