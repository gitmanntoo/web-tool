"""
Pytest fixtures for web-tool integration tests.

Provides:
- app_client: Flask test client
- test_page_builder: helper to build test page URLs with query params
"""

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from urllib.parse import urlencode

import pytest


def _load_web_tool():
    """Load web-tool.py as a module despite the hyphenated name."""
    app_path = Path(__file__).resolve().parent.parent / "web-tool.py"
    spec = spec_from_file_location("web_tool", app_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load loader for {app_path} (from {__file__})")
    web_tool = module_from_spec(spec)
    spec.loader.exec_module(web_tool)
    return web_tool


# Load web-tool module once for all fixtures
_web_tool = _load_web_tool()
app = _web_tool.app


@pytest.fixture
def app_client():
    """Flask application test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def base_url():
    """Base URL prefix for test pages."""
    return "/test-page"


@pytest.fixture
def test_page_builder(base_url):
    """
    Returns a callable that builds test page URLs.

    Usage:
        url = test_page_builder(title="Hello", fragment="section1")
    """

    def _build_url(**params):
        if not params:
            return base_url
        filtered = {k: v for k, v in params.items() if v is not None and v != ""}
        if not filtered:
            return base_url
        return f"{base_url}?{urlencode(filtered, doseq=True)}"

    return _build_url
