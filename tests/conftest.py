"""
Pytest fixtures for web-tool integration tests.

Provides:
- app_client: Flask test client
- test_page_builder: helper to build test page URLs with query params
"""

import importlib.util

import pytest


def _load_web_tool():
    """Load web-tool.py as a module despite the hyphenated name."""
    spec = importlib.util.spec_from_file_location("web_tool", "web-tool.py")
    web_tool = importlib.util.module_from_spec(spec)
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
        query_parts = []
        for key, value in params.items():
            if value is not None and value != "":
                query_parts.append(f"{key}={value}")
        if not query_parts:
            return base_url
        return f"{base_url}?{'&'.join(query_parts)}"

    return _build_url
