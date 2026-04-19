"""
Tests for clipboard loading in PageMetadata.

Tests stale batch_id handling and PyperclipException recovery
in environments without a clipboard mechanism (e.g. Docker).
"""

from unittest.mock import MagicMock, patch

import pyperclip
import pytest

from library.util import PageMetadata, clip_cache


def _make_mock_request(**overrides):
    """Create a mock Flask request with sensible defaults."""
    defaults = {
        "url": "https://example.com",
        "title": "Test",
        "format": "html",
        "batchId": "",
        "textLength": "0",
        "clipboardError": "",
        "contentType": "",
    }
    defaults.update(overrides)
    mock_request = MagicMock()
    mock_request.args.get.side_effect = lambda key, default=None: defaults.get(key, default)
    mock_request.headers = {}
    return mock_request


class TestStaleBatchId:
    """When batch_id is present but not in clip_cache, load_clipboard should
    set clipboard_error instead of falling through to pyperclip.paste()."""

    def test_stale_batch_sets_clipboard_error(self):
        """Stale batch_id (not in cache) sets clipboard_error, no pyperclip call."""
        mock_request = _make_mock_request(batchId="stale-batch-id")

        with patch.object(pyperclip, "paste") as mock_paste:
            metadata = PageMetadata(request=mock_request)
            # pyperclip.paste should NOT be called for stale batch
            mock_paste.assert_not_called()

        assert metadata.clipboard_error == "stale_batch"

    def test_valid_batch_loads_normally(self):
        """Valid batch_id in clip_cache loads data and clears the batch."""
        import time

        batch_id = "valid-batch-id"
        clip_cache[batch_id] = {
            "chunks": {0: "test clipboard content"},
            "created_at": time.time(),
        }
        mock_request = _make_mock_request(batchId=batch_id, textLength="22")

        metadata = PageMetadata(request=mock_request)
        assert metadata.mirror_data is not None
        assert metadata.clipboard_error == ""
        # Batch should be consumed
        assert batch_id not in clip_cache


class TestPyperclipException:
    """When no batch_id and pyperclip is unavailable, load_clipboard should
    set clipboard_error instead of crashing."""

    def test_no_clipball_sets_clipboard_error(self):
        """PyperclipException in Docker sets clipboard_error gracefully."""
        mock_request = _make_mock_request()

        with patch.object(
            pyperclip, "paste",
            side_effect=pyperclip.PyperclipException("no clipboard"),
        ):
            metadata = PageMetadata(request=mock_request)

        assert metadata.clipboard_error == "clipboard_unavailable"

    def test_no_batch_with_working_clipboard(self):
        """No batch_id with working clipboard loads data normally."""
        mock_request = _make_mock_request()

        with patch.object(pyperclip, "paste", return_value="clipboard content"):
            metadata = PageMetadata(request=mock_request)

        assert metadata.mirror_data is not None
        assert metadata.clipboard_error == ""


class TestExistingClipboardError:
    """When clipboardError is already set in request args, load_clipboard should
    skip both batch and pyperclip paths."""

    def test_existing_error_skips_clipboard(self):
        """Pre-existing clipboardError triggers fallback URL fetch."""
        mock_request = _make_mock_request(clipboardError="some error")

        with patch.object(pyperclip, "paste") as mock_paste:
            with patch("library.util.url_util.get_url") as mock_get_url:
                mock_get_url.return_value = MagicMock(error="not found", content_type="text/html")
                metadata = PageMetadata(request=mock_request)
                mock_paste.assert_not_called()

        assert metadata.clipboard_error == "some error"




if __name__ == "__main__":
    pytest.main([__file__, "-v"])
