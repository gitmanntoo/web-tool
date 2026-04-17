"""JavaScript serving routes."""

from flask import Blueprint, abort, current_app, request

from library import util

bp = Blueprint("javascript", __name__)


@bp.route("/js/<filename>.js")
def serve_js(filename):
    """
    Serves javascript files from the static directory.
    Mode controls the output format:
    - "minify": minified javascript
    - "bookmarklet": a bookmarklet from minified javascript
    - default: unmodified javascript
    """
    # Ensure the filename does not contain path traversals
    if ".." in filename or filename.startswith("/"):
        abort(404)  # Not found

    template_env = current_app.template_env

    # Read options
    mode = request.args.get("mode", "")
    format = request.args.get("format", "html")

    # Return the contents
    out_str = util.get_javascript_file(
        filename,
        mode,
        template_env=template_env,
        format=format,
    )

    return util.plain_text_response(
        template_env,
        f"{filename}.js",
        out_str,
        format="html",
        language="javascript",
    )
