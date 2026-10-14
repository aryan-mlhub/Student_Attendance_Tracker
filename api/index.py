import sys
from pathlib import Path
from werkzeug.middleware.proxy_fix import ProxyFix

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app as flask_app

# Enable ProxyFix to correctly handle Vercel HTTPS reverse proxy headers
flask_app.wsgi_app = ProxyFix(
    flask_app.wsgi_app,
    x_for=1,
    x_proto=1,
    x_host=1,
    x_prefix=1
)


class VercelPathFixer:
    """WSGI middleware to adapt Vercel serverless rewrite paths to standard Flask routes."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Extract the user's real requested URI from Vercel's WSGI environment
        raw_uri = (
            environ.get("REQUEST_URI")
            or environ.get("RAW_URI")
            or environ.get("HTTP_X_FORWARDED_PATH")
        )

        if raw_uri:
            # Strip query parameters to get clean path
            path = raw_uri.split("?")[0]
            if path.startswith("/api/index"):
                path = path[len("/api/index"):] or "/"
            environ["PATH_INFO"] = path
        elif environ.get("PATH_INFO") in ("/api/index", "/api/index.py", "/api"):
            environ["PATH_INFO"] = "/"

        return self.wsgi_app(environ, start_response)


app = VercelPathFixer(flask_app)
