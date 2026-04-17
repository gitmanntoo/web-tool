import logging

from flask import Flask
from jinja2 import Environment, FileSystemLoader

from library import docker_util, util
from routes import debug, javascript, mirror_favicons, mirror_links

app = Flask(__name__)

# Initialize template environment.
template_loader = FileSystemLoader(util.TEMPLATE_DIR)
template_env = Environment(loader=template_loader)
app.template_env = template_env

# Register route blueprints.
app.register_blueprint(mirror_links.bp)
app.register_blueprint(mirror_favicons.bp)
app.register_blueprint(debug.bp)
app.register_blueprint(javascript.bp)


@app.before_request
def before_request_cleanup():
    """Clean up expired clip_cache entries before each request."""
    util.cleanup_clip_cache()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


if __name__ == "__main__":
    if docker_util.is_running_in_container():
        port = 8532
        debug_flag = False
    else:
        port = 8535
        debug_flag = True

    app.run(host="0.0.0.0", port=port, debug=debug_flag)
