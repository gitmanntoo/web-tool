"""Flask route blueprints for the web-tool application."""

import json


def json_response(data: dict, status: int = 200) -> tuple:
    """Create a Flask JSON response tuple."""
    return json.dumps(data), status, {"Content-Type": "application/json"}
