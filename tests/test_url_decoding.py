"""
Tests for URL encoding/decoding in PageMetadata.

Tests that URLs from the bookmarklet (which are URL-encoded) are properly
decoded before parsing to handle fragments containing special characters.
"""

from unittest.mock import MagicMock

import pytest

from library.util import PageMetadata


class TestPageMetadataUrlDecoding:
    """Tests for URL decoding in PageMetadata."""

    def _make_mock_request(self, url):
        """Create a mock Flask request with the given URL."""
        mock_request = MagicMock()
        mock_request.args.get.side_effect = lambda key, default=None: {
            "url": url,
            "title": "Test Title",
            "format": "html",
        }.get(key, default)
        mock_request.headers = {}
        return mock_request

    def test_url_with_fragment_containing_dots_is_decoded(self):
        """Test that URL with fragment containing dots is properly decoded."""
        # This is the URL-encoded form that comes from the bookmarklet
        encoded_url = (
            "https%3A%2F%2Fpydantic.com.cn%2Fen%2Fapi%2Fjson_schema%2F"
            "%23pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method"
        )
        expected_url = (
            "https://pydantic.com.cn/en/api/json_schema/"
            "#pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method"
        )

        mock_request = self._make_mock_request(encoded_url)
        metadata = PageMetadata(request=mock_request)

        # URL should be decoded
        assert metadata.url == expected_url
        # Fragment should be extracted correctly
        assert metadata.parsed_url.fragment == "pydantic.json_schema.GenerateJsonSchema.build_schema_type_to_method"

    def test_url_without_fragment_is_decoded(self):
        """Test that URL without fragment is properly decoded."""
        encoded_url = "https%3A%2F%2Fexample.com%2Fpath%2Fpage"
        expected_url = "https://example.com/path/page"

        mock_request = self._make_mock_request(encoded_url)
        metadata = PageMetadata(request=mock_request)

        assert metadata.url == expected_url
        assert metadata.parsed_url.fragment == ""

    def test_url_with_query_string_is_decoded(self):
        """Test that URL with query string is properly decoded."""
        encoded_url = "https%3A%2F%2Fexample.com%2Fsearch%3Fq%3Dtest%2Bvalue"
        expected_url = "https://example.com/search?q=test+value"

        mock_request = self._make_mock_request(encoded_url)
        metadata = PageMetadata(request=mock_request)

        assert metadata.url == expected_url

    def test_url_with_percent_in_fragment_is_decoded(self):
        """Test that URL with %23 in fragment (encoded #) is decoded to #."""
        # %23 is the URL-encoded form of #
        encoded_url = "https%3A%2F%2Fexample.com%2Fpage%23section%2Fsub"
        expected_url = "https://example.com/page#section/sub"

        mock_request = self._make_mock_request(encoded_url)
        metadata = PageMetadata(request=mock_request)

        assert metadata.url == expected_url
        assert metadata.parsed_url.fragment == "section/sub"

    def test_url_already_decoded_is_unchanged(self):
        """Test that already-decoded URL passes through unchanged."""
        url = "https://example.com/path#fragment"

        mock_request = self._make_mock_request(url)
        metadata = PageMetadata(request=mock_request)

        assert metadata.url == url
        assert metadata.parsed_url.fragment == "fragment"

    def test_empty_url_handled(self):
        """Test that empty URL is handled gracefully."""
        mock_request = self._make_mock_request("")
        metadata = PageMetadata(request=mock_request)

        assert metadata.url == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
