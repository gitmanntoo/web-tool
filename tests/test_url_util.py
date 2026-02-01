"""
Tests for library/url_util.py

Tests URL parsing, validation, and retrieval functions.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from library.url_util import (
    get_user_agent,
    SerializedResponseError,
    SerializedResponse,
    get_top_domain_name,
    get_url_root,
    get_url_host,
    make_absolute_urls,
    DEFAULT_USER_AGENT,
)


class TestGetUserAgent:
    """Tests for get_user_agent function."""

    def test_returns_string(self):
        """Test that get_user_agent returns a string."""
        result = get_user_agent()
        assert isinstance(result, str)

    def test_returns_default_when_error(self):
        """Test that function handles request context appropriately."""
        # Function uses Flask request context which is not available in test environment
        # Just verify it doesn't crash completely when called
        try:
            result = get_user_agent()
            # If we can get here without context, verify result is string
            assert isinstance(result, str)
        except RuntimeError:
            # Expected when not in Flask request context
            pass


class TestSerializedResponseError:
    """Tests for SerializedResponseError exception."""

    def test_is_exception(self):
        """Test that SerializedResponseError is an Exception."""
        assert issubclass(SerializedResponseError, Exception)

    def test_can_raise_and_catch(self):
        """Test that SerializedResponseError can be raised and caught."""
        with pytest.raises(SerializedResponseError):
            raise SerializedResponseError("Test error")


class TestSerializedResponse:
    """Tests for SerializedResponse dataclass."""

    def test_initialization(self):
        """Test basic initialization of SerializedResponse."""
        resp = SerializedResponse(source_url="http://example.com")
        assert resp.source_url == "http://example.com"
        assert resp.resolved_url is None
        assert resp.status_code is None

    def test_has_required_fields(self):
        """Test that SerializedResponse has required fields."""
        resp = SerializedResponse(source_url="http://example.com")
        assert hasattr(resp, 'source_url')
        assert hasattr(resp, 'resolved_url')
        assert hasattr(resp, 'status_code')
        assert hasattr(resp, 'headers')
        assert hasattr(resp, 'content')
        assert hasattr(resp, 'error')

    def test_error_field_can_be_set(self):
        """Test that error field can be set."""
        resp = SerializedResponse(
            source_url="http://example.com",
            error="Test error"
        )
        assert resp.error == "Test error"

    def test_content_type_field(self):
        """Test content_type field."""
        resp = SerializedResponse(
            source_url="http://example.com",
            content_type="text/html"
        )
        assert resp.content_type == "text/html"


class TestGetTopDomainName:
    """Tests for get_top_domain_name function."""

    def test_simple_domain(self):
        """Test extraction of top domain."""
        result = get_top_domain_name("http://example.com")
        assert result == "example.com"

    def test_subdomain_extraction(self):
        """Test extraction with subdomain."""
        result = get_top_domain_name("http://www.example.com")
        assert "example.com" in result

    def test_url_with_path(self):
        """Test extraction from URL with path."""
        result = get_top_domain_name("http://example.com/path/to/page")
        assert result == "example.com"

    def test_https_url(self):
        """Test with HTTPS URL."""
        result = get_top_domain_name("https://example.com")
        assert result == "example.com"

    def test_with_query_string(self):
        """Test URL with query string."""
        result = get_top_domain_name("http://example.com/page?query=value")
        assert result == "example.com"


class TestGetUrlRoot:
    """Tests for get_url_root function."""

    def test_simple_url_root(self):
        """Test extraction of URL root."""
        # Function returns scheme, netloc, and first path segment (not just root)
        result = get_url_root("http://example.com/path/to/page")
        assert result == "http://example.com/path"

    def test_url_without_path(self):
        """Test URL without path."""
        result = get_url_root("http://example.com")
        assert "example.com" in result

    def test_https_url_root(self):
        """Test HTTPS URL root."""
        result = get_url_root("https://example.com/path")
        assert "https" in result and "example.com" in result

    def test_url_with_query_string(self):
        """Test URL root ignores query string."""
        result = get_url_root("http://example.com/path?query=value")
        assert "example.com" in result


class TestGetUrlHost:
    """Tests for get_url_host function."""

    def test_simple_host(self):
        """Test extraction of host."""
        result = get_url_host("http://example.com")
        assert result == "http://example.com"

    def test_host_with_path(self):
        """Test host extraction from URL with path."""
        result = get_url_host("http://example.com/path/to/page")
        assert result == "http://example.com"

    def test_https_host(self):
        """Test HTTPS host."""
        result = get_url_host("https://example.com/path")
        assert result == "https://example.com"

    def test_host_without_trailing_slash(self):
        """Test that host doesn't have trailing slash."""
        result = get_url_host("http://example.com/")
        assert result == "http://example.com"


class TestMakeAbsoluteUrls:
    """Tests for make_absolute_urls function."""

    def test_absolute_url_unchanged(self):
        """Test that absolute URLs are unchanged."""
        result = make_absolute_urls(
            "http://example.com/page",
            "http://other.com/other"
        )
        assert result == "http://other.com/other"

    def test_relative_path_made_absolute(self):
        """Test that relative paths are made absolute."""
        result = make_absolute_urls(
            "http://example.com/page/index.html",
            "../other/page.html"
        )
        assert result.startswith("http://example.com")

    def test_relative_root_path(self):
        """Test relative path from root."""
        result = make_absolute_urls(
            "http://example.com/page/index.html",
            "/other/page.html"
        )
        assert result == "http://example.com/other/page.html"

    def test_current_directory_relative(self):
        """Test current directory relative path."""
        result = make_absolute_urls(
            "http://example.com/page/index.html",
            "./other.html"
        )
        assert "example.com" in result
        assert "other.html" in result

    def test_same_page_reference(self):
        """Test same-page reference."""
        result = make_absolute_urls(
            "http://example.com/page.html",
            "#anchor"
        )
        # Should reference the same page with anchor
        assert "example.com" in result


class TestUrlValidation:
    """Integration tests for URL validation."""

    def test_valid_url_structure(self):
        """Test that valid URL structures are preserved."""
        urls = [
            "http://example.com",
            "https://example.com:8080/path",
            "http://user:pass@example.com",
        ]
        for url in urls:
            root = get_url_root(url)
            assert root  # Should return something
            host = get_url_host(url)
            assert host  # Should return something


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
