from flask import Flask, abort, request, make_response
from jinja2 import Environment, FileSystemLoader
import markdown
import pyperclip

from library import util

app = Flask(__name__)

# Initialize template environment.
template_loader = FileSystemLoader(util.TEMPLATE_DIR)
template_env = Environment(loader=template_loader)

@app.route('/')
def read_root():
    return markdown.markdown(open("README.md").read())


@app.route('/js/<filename>.js')
def serve_js(filename):
    """
    Serves javascript files from the static directory.
    Mode controls the output format:
    - "minify": minified javascript
    - "bookmarklet": a bookmarklet from minified javascript
    - default: unmodified javascript
    """
    # Ensure the filename does not contain path traversals
    if '..' in filename or filename.startswith('/'):
        abort(404)  # Not found

    # Read options
    mode = request.args.get("mode", "")
    # Return the contents
    outStr = util.get_javascript_file(
        filename, mode, template_env=template_env
    )
    pyperclip.copy(outStr)

    response = make_response(outStr)
    response.headers['Content-Type'] = 'text/plain'
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8532)
