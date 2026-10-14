import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app as flask_app


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
            if path in ("", "/", "/api", "/api/index", "/api/index.py"):
                environ["PATH_INFO"] = "/dashboard"
            elif path.startswith("/api/index/"):
                environ["PATH_INFO"] = path[len("/api/index"):] or "/dashboard"
            else:
                environ["PATH_INFO"] = path
        elif environ.get("PATH_INFO") in ("", "/", "/api", "/api/index", "/api/index.py"):
            environ["PATH_INFO"] = "/dashboard"

        return self.wsgi_app(environ, start_response)


app = VercelPathFixer(flask_app)
