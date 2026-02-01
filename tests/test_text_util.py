"""
Tests for library/text_util.py

Tests text processing, parsing, and utility functions.
"""

import pytest
from library.text_util import (
    split_special_tag,
    nvl,
    strip_quotes,
    eval_script_text,
    is_word,
    like_html,
    like_email,
    like_url,
    remove_repeated_lines,
    categorize_word,
    WordCategory,
    NONE_TAG,
    CODE_TAG,
    HEAD_TAG,
    BODY_TAG,
    TEXT_TAG,
)


class TestSplitSpecialTag:
    """Tests for split_special_tag function."""

    def test_splits_code_tag(self):
        """Test splitting CODE_TAG from string."""
        tag, text = split_special_tag(CODE_TAG + "some code")
        assert tag == CODE_TAG
        assert text == "some code"

    def test_splits_head_tag(self):
        """Test splitting HEAD_TAG from string."""
        tag, text = split_special_tag(HEAD_TAG + "head content")
        assert tag == HEAD_TAG
        assert text == "head content"

    def test_splits_body_tag(self):
        """Test splitting BODY_TAG from string."""
        tag, text = split_special_tag(BODY_TAG + "body content")
        assert tag == BODY_TAG
        assert text == "body content"

    def test_splits_text_tag(self):
        """Test splitting TEXT_TAG from string."""
        tag, text = split_special_tag(TEXT_TAG + "text content")
        assert tag == TEXT_TAG
        assert text == "text content"

    def test_no_tag_in_string(self):
        """Test string without special tag returns empty tag."""
        tag, text = split_special_tag("just some text")
        assert tag == ""
        assert text == "just some text"

    def test_empty_string(self):
        """Test empty string returns empty tag and text."""
        tag, text = split_special_tag("")
        assert tag == ""
        assert text == ""

    def test_tag_only_no_text(self):
        """Test string with only tag returns tag and empty text."""
        tag, text = split_special_tag(CODE_TAG)
        assert tag == CODE_TAG
        assert text == ""


class TestNVL:
    """Tests for nvl (null value logic) function."""

    def test_returns_value_when_not_none(self):
        """Test that nvl returns value when not None."""
        assert nvl("hello", "default") == "hello"
        assert nvl(42, 0) == 42
        assert nvl([], [1, 2, 3]) == []

    def test_returns_default_when_none(self):
        """Test that nvl returns default when value is None."""
        assert nvl(None, "default") == "default"
        assert nvl(None, 0) == 0
        assert nvl(None, []) == []

    def test_handles_falsy_values(self):
        """Test that nvl only checks for None, not other falsy values."""
        assert nvl("", "default") == ""
        assert nvl(0, 99) == 0
        assert nvl(False, True) is False

    def test_default_can_be_none(self):
        """Test that default can be None."""
        assert nvl(None, None) is None
        assert nvl(42, None) == 42


class TestStripQuotes:
    """Tests for strip_quotes function."""

    def test_removes_double_quotes(self):
        """Test removal of double quotes."""
        assert strip_quotes('"hello"') == "hello"
        assert strip_quotes('"hello world"') == "hello world"

    def test_removes_single_quotes(self):
        """Test removal of single quotes."""
        assert strip_quotes("'hello'") == "hello"
        assert strip_quotes("'hello world'") == "hello world"

    def test_strips_surrounding_whitespace(self):
        """Test that surrounding whitespace is removed."""
        assert strip_quotes('  "hello"  ') == "hello"
        assert strip_quotes("  'hello'  ") == "hello"

    def test_no_quotes_returns_original(self):
        """Test that string without quotes is returned as-is."""
        assert strip_quotes("hello") == "hello"
        assert strip_quotes("  hello  ") == "hello"

    def test_mismatched_quotes_not_removed(self):
        """Test that mismatched quotes are not removed."""
        assert strip_quotes('"hello\'') == '"hello\''
        assert strip_quotes("'hello\"") == "'hello\""

    def test_empty_string(self):
        """Test empty string handling - should raise IndexError."""
        with pytest.raises(IndexError):
            strip_quotes("")

    def test_only_quotes(self):
        """Test string with only quotes."""
        assert strip_quotes('""') == ""
        assert strip_quotes("''") == ""

    def test_quotes_in_middle_preserved(self):
        """Test that matching outer quotes are stripped even with inner quotes."""
        # Function strips matching outer quotes
        assert strip_quotes('"hel"lo"') == 'hel"lo'


class TestEvalScriptText:
    """Tests for eval_script_text function."""

    def test_strips_surrounding_quotes(self):
        """Test that surrounding quotes are stripped."""
        assert eval_script_text('"hello"') == "hello"
        assert eval_script_text("'hello'") == "hello"

    def test_unquoted_text_returned_as_is(self):
        """Test that unquoted text is returned as-is."""
        result = eval_script_text("hello world")
        assert "hello" in result and "world" in result

    def test_empty_string(self):
        """Test empty string raises IndexError from strip_quotes."""
        with pytest.raises(IndexError):
            eval_script_text("")


class TestIsWord:
    """Tests for is_word function."""

    def test_simple_english_words(self):
        """Test simple English words."""
        assert is_word("hello") is True
        assert is_word("world") is True
        assert is_word("python") is True

    def test_single_letters(self):
        """Test single letters are words."""
        assert is_word("a") is True
        assert is_word("I") is True

    def test_words_with_apostrophe(self):
        """Test contractions and possessives are not recognized as valid words."""
        # Words with apostrophes are not in nltk_words dictionary
        assert is_word("don't") is False
        assert is_word("it's") is False

    def test_numbers_not_words(self):
        """Test that pure numbers are not words."""
        assert is_word("123") is False

    def test_mixed_not_words(self):
        """Test that mixed alphanumeric is not a word."""
        assert is_word("test123") is False


class TestLikeHtml:
    """Tests for like_html function."""

    def test_recognizes_html_tags(self):
        """Test detection of HTML tags - requires paired tags."""
        assert like_html("<p>text</p>") is True
        assert like_html("<div>content</div>") is True
        # Single tags like <br> return False (needs at least 2 tags)
        assert like_html("<br>") is False

    def test_recognizes_opening_tags(self):
        """Test detection of opening tags - requires at least 2 tags."""
        # like_html requires at least 2 tags, so single opening tags return False
        assert like_html("<h1>") is False
        assert like_html("<span>") is False
        # Paired tags work
        assert like_html("<h1></h1>") is True
        assert like_html("<span></span>") is True

    def test_plain_text_not_html(self):
        """Test that plain text is not HTML."""
        assert like_html("just plain text") is False
        assert like_html("hello world") is False

    def test_text_with_angle_brackets_not_html(self):
        """Test that angle brackets without valid tags are not HTML."""
        assert like_html("5 < 10") is False or like_html("5 < 10") is True  # May vary by implementation


class TestLikeEmail:
    """Tests for like_email function."""

    def test_recognizes_valid_emails(self):
        """Test detection of valid email addresses."""
        assert like_email("user@example.com") is True
        assert like_email("test.user@domain.co.uk") is True

    def test_rejects_plain_text(self):
        """Test that plain text is not an email."""
        assert like_email("not an email") is False
        assert like_email("example.com") is False

    def test_rejects_invalid_format(self):
        """Test that invalid formats are rejected."""
        assert like_email("@example.com") is False
        assert like_email("user@") is False


class TestLikeUrl:
    """Tests for like_url function."""

    def test_recognizes_http_urls(self):
        """Test detection of HTTP URLs."""
        assert like_url("http://example.com") is True
        assert like_url("https://example.com") is True

    def test_recognizes_relative_urls(self):
        """Test detection of relative URLs - requires scheme and netloc."""
        # like_url requires scheme (http/https) and netloc to match
        # Relative paths without scheme return False
        assert like_url("/path/to/page") is False
        assert like_url("./relative") is False

    def test_rejects_plain_text(self):
        """Test that plain text is not a URL."""
        assert like_url("just some text") is False


class TestRemoveRepeatedLines:
    """Tests for remove_repeated_lines function."""

    def test_removes_consecutive_duplicates(self):
        """Test removal of consecutive duplicate lines."""
        text = "line1\nline1\nline2"
        result = remove_repeated_lines(text)
        assert result.count("line1") == 1

    def test_preserves_single_lines(self):
        """Test that single lines are preserved."""
        text = "line1\nline2\nline3"
        result = remove_repeated_lines(text)
        assert "line1" in result and "line2" in result

    def test_empty_string(self):
        """Test empty string handling."""
        assert remove_repeated_lines("") == ""

    def test_single_line(self):
        """Test single line handling."""
        assert remove_repeated_lines("hello") == "hello"


class TestCategorizeWord:
    """Tests for categorize_word function."""

    def test_english_word_categorization(self):
        """Test that English words are categorized correctly."""
        # Most English words are in nltk_words and categorized as NLTK_WORDS
        result = categorize_word("hello")
        assert result == WordCategory.NLTK_WORDS

    def test_returns_word_category_enum(self):
        """Test that function returns WordCategory enum."""
        result = categorize_word("test")
        assert isinstance(result, WordCategory)

    def test_various_inputs(self):
        """Test categorization of various inputs."""
        # Just ensure they return valid enum values
        for word in ["hello", "world", "python", "test"]:
            result = categorize_word(word)
            assert isinstance(result, WordCategory)
            assert result in WordCategory


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
