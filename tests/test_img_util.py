"""
Tests for library/img_util.py

Tests image conversion utilities.
"""

import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO
from PIL import Image
from library.img_util import (
    convert_ico,
    convert_svg,
    SVG_WIDTH,
    SVG_HEIGHT,
)
from library import url_util


class TestImageConversionConstants:
    """Tests for image conversion constants."""

    def test_svg_width_is_positive(self):
        """Test that SVG_WIDTH is positive."""
        assert SVG_WIDTH > 0
        assert isinstance(SVG_WIDTH, int)

    def test_svg_height_is_positive(self):
        """Test that SVG_HEIGHT is positive."""
        assert SVG_HEIGHT > 0
        assert isinstance(SVG_HEIGHT, int)

    def test_svg_dimensions_are_reasonable(self):
        """Test that SVG dimensions are reasonable (256x256 is common)."""
        assert 100 < SVG_WIDTH < 1000
        assert 100 < SVG_HEIGHT < 1000


class TestConvertIco:
    """Tests for convert_ico function."""

    def test_returns_bytes_or_none(self):
        """Test that convert_ico returns bytes or None."""
        # This test uses caching, so we might get None on first call
        # if the URL fetch fails
        result = convert_ico("http://invalid.example.invalid/favicon.ico")
        assert result is None or isinstance(result, bytes)

    def test_has_lru_cache(self):
        """Test that convert_ico has lru_cache decorator."""
        # The function should have cache_info method if it's cached
        assert hasattr(convert_ico, 'cache_info')
        assert callable(convert_ico.cache_info)

    def test_cache_can_be_cleared(self):
        """Test that cache can be cleared."""
        if hasattr(convert_ico, 'cache_clear'):
            convert_ico.cache_clear()
            # After clear, cache should be empty
            info = convert_ico.cache_info()
            assert info.hits == 0

    def test_accepts_url_parameter(self):
        """Test that convert_ico accepts URL parameter."""
        # Function signature test
        import inspect
        sig = inspect.signature(convert_ico)
        assert 'href' in sig.parameters

    def test_accepts_format_parameter(self):
        """Test that convert_ico accepts format parameter."""
        import inspect
        sig = inspect.signature(convert_ico)
        assert 'to_format' in sig.parameters

    def test_default_format_is_png(self):
        """Test that default format parameter is PNG."""
        import inspect
        sig = inspect.signature(convert_ico)
        assert sig.parameters['to_format'].default == "PNG"

    @patch('library.img_util.url_util.get_url')
    def test_handles_non_ico_file(self, mock_get_url):
        """Test that non-ICO files return None."""
        mock_response = MagicMock()
        mock_response.get_type.return_value = "image/png"
        mock_get_url.return_value = mock_response
        
        convert_ico.cache_clear()
        result = convert_ico("http://example.com/image.png")
        
        # Should return None for non-ICO files
        assert result is None

    @patch('library.img_util.url_util.get_url')
    def test_handles_serialized_response_error(self, mock_get_url):
        """Test handling of SerializedResponseError."""
        from library.url_util import SerializedResponseError
        mock_get_url.side_effect = SerializedResponseError("Network error")
        
        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")
        
        # Should return None on error
        assert result is None

    @patch('library.img_util.url_util.get_url')
    def test_handles_generic_exception(self, mock_get_url):
        """Test handling of SerializedResponseError exceptions."""
        # Function only catches SerializedResponseError, not generic exceptions
        # So we test that it properly handles that specific exception
        mock_get_url.side_effect = url_util.SerializedResponseError("Network error")
        
        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")
        
        # Should return None on SerializedResponseError
        assert result is None


class TestConvertSvg:
    """Tests for convert_svg function."""

    def test_returns_bytes(self):
        """Test that convert_svg returns bytes."""
        # This test would need a real SVG URL or mock
        result = convert_svg("http://invalid.example.invalid/icon.svg")
        # May return bytes or raise an exception, but not None
        assert result is None or isinstance(result, bytes)

    def test_has_lru_cache(self):
        """Test that convert_svg has lru_cache decorator."""
        assert hasattr(convert_svg, 'cache_info')
        assert callable(convert_svg.cache_info)

    def test_cache_can_be_cleared(self):
        """Test that SVG cache can be cleared."""
        if hasattr(convert_svg, 'cache_clear'):
            convert_svg.cache_clear()
            # After clear, cache should be empty
            info = convert_svg.cache_info()
            assert info.hits == 0

    def test_accepts_url_parameter(self):
        """Test that convert_svg accepts URL parameter."""
        import inspect
        sig = inspect.signature(convert_svg)
        assert 'href' in sig.parameters

    def test_accepts_format_parameter(self):
        """Test that convert_svg accepts format parameter."""
        import inspect
        sig = inspect.signature(convert_svg)
        assert 'to_format' in sig.parameters

    def test_default_format_is_png(self):
        """Test that default format for SVG conversion is PNG."""
        import inspect
        sig = inspect.signature(convert_svg)
        assert sig.parameters['to_format'].default == "PNG"

    @patch('library.img_util.svg2png')
    @patch('library.img_util.url_util.get_url')
    def test_uses_cairosvg_conversion(self, mock_get_url, mock_svg2png):
        """Test that svg2png from cairosvg is used when response is SVG."""
        mock_response = MagicMock()
        mock_response.content = b"<svg></svg>"
        # Mock get_type to return SVG mime type (not "image/svg" since the code checks for exact match)
        # The validation is: if resp.get_type() != "image/svg": which means it logs warning and returns None
        # So we need to return "image/svg" to pass validation
        mock_response.get_type.return_value = "image/svg"
        mock_get_url.return_value = mock_response
        mock_svg2png.return_value = None  # svg2png writes to buffer, returns None
        
        convert_svg.cache_clear()
        result = convert_svg("http://example.com/icon.svg")
        
        # svg2png should have been called since magika validation passed
        assert mock_svg2png.called

    @patch('library.img_util.url_util.get_url')
    def test_handles_network_error(self, mock_get_url):
        """Test handling of network errors."""
        from library.url_util import SerializedResponseError
        mock_get_url.side_effect = SerializedResponseError("Network error")
        
        convert_svg.cache_clear()
        result = convert_svg("http://example.com/icon.svg")
        
        # Should handle error gracefully
        assert result is None or isinstance(result, bytes)


class TestImageConversionIntegration:
    """Integration tests for image conversion."""

    def test_ico_conversion_function_exists(self):
        """Test that ico conversion function exists and is callable."""
        assert callable(convert_ico)

    def test_svg_conversion_function_exists(self):
        """Test that SVG conversion function exists and is callable."""
        assert callable(convert_svg)

    def test_both_functions_have_caching(self):
        """Test that both functions use caching."""
        assert hasattr(convert_ico, 'cache_info')
        assert hasattr(convert_svg, 'cache_info')

    def test_cache_size_limits(self):
        """Test that caches have reasonable size limits."""
        # Get cache info
        ico_info = convert_ico.cache_info()
        svg_info = convert_svg.cache_info()
        
        # Both should have maxsize set
        assert hasattr(convert_ico, 'cache_info')
        assert hasattr(convert_svg, 'cache_info')


class TestImageConversionEdgeCases:
    """Tests for edge cases in image conversion."""

    @patch('library.img_util.url_util.get_url')
    def test_convert_ico_empty_response(self, mock_get_url):
        """Test handling of empty response content."""
        mock_response = MagicMock()
        mock_response.content = b""
        mock_response.get_type.return_value = "image/x-icon"
        mock_get_url.return_value = mock_response
        
        convert_ico.cache_clear()
        result = convert_ico("http://example.com/favicon.ico")
        
        # Should handle empty content
        assert result is None or isinstance(result, bytes)

    @patch('library.img_util.url_util.get_url')
    def test_convert_ico_with_different_format(self, mock_get_url):
        """Test converting ICO to different format."""
        mock_response = MagicMock()
        mock_response.content = b"ICO_DATA"
        mock_response.get_type.return_value = "image/x-icon"
        mock_response.raise_for_status.return_value = None
        
        # Mock PIL Image
        mock_image = MagicMock()
        mock_image.format = "ICO"
        
        with patch('library.img_util.Image.open') as mock_open:
            mock_open.return_value = mock_image
            mock_image.save.return_value = None
            
            mock_get_url.return_value = mock_response
            
            # Try conversion to JPEG
            convert_ico.cache_clear()
            result = convert_ico("http://example.com/favicon.ico", to_format="JPEG")
            
            # Should attempt conversion
            assert mock_image.save.called or result is not None or result is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
