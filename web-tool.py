from flask import Flask, abort, request, make_response
from jinja2 import Environment, FileSystemLoader
import json
import markdown
import pyperclip

from library import util

app = Flask(__name__)

# Initialize template environment.
template_loader = FileSystemLoader(util.TEMPLATE_DIR)
template_env = Environment(loader=template_loader)

@app.route('/')
def read_root():
    """Display the README file."""
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

    return util.plain_text_response(template_env, f"{filename}.js", outStr)


@app.route('/clip-proxy', methods=['GET'])
def clip_to_post():
    """Copy the contents of a the clipboard into a POST request."""
    template = template_env.get_template('clip-proxy.html')
    rendered_html = template.render({})

    resp = make_response(rendered_html)
    return resp


@app.route('/clip-collector', methods=['POST'])
def clip_collector():
    """Collect chunks of text by batch ID and chunk number."""

    # Read headers.
    batch_id = request.args.get('batchId')
    chunk_number = int(request.args.get('chunkNum'))

    chunk_dict = util.clip_cache.setdefault(batch_id, {})
    chunk_dict[chunk_number] = request.data.decode()

    return "OK"


@app.route('/mirror-clip', methods=['POST'])
def mirror_clip():
    """Copy the contents of a post request into the clipboard."""

    metadata = util.get_page_metadata()

    # Read clipboard contents.
    clip = metadata["clipboard"]

    # If clip is valid JSON, format it with indentation.
    clip_text = clip
    try:
        clip_json = json.loads(clip)
        clip_text = json.dumps(clip_json, indent=2)
    except json.JSONDecodeError:
        pass

    return util.plain_text_response(template_env, "Clipboard Contents", clip_text)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8532, debug=True)
