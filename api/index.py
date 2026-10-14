import sys
from pathlib import Path

# Add project root directory to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from app import app as flask_app


class VercelPathMiddleware:
    """WSGI middleware to adapt Vercel rewrite paths to standard Flask routes."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # Vercel sets the original user-requested path in HTTP_X_MATCHED_PATH
        matched_path = (
            environ.get("HTTP_X_MATCHED_PATH")
            or environ.get("HTTP_X_FORWARDED_PATH")
            or environ.get("PATH_INFO", "")
        )

        if matched_path in ("/api/index", "/api/index.py", "/api", ""):
            environ["PATH_INFO"] = "/"
        elif matched_path.startswith("/api/index/"):
            environ["PATH_INFO"] = matched_path[len("/api/index"):]
        elif matched_path.startswith("/api/"):
            environ["PATH_INFO"] = matched_path[len("/api"):]
        elif matched_path:
            environ["PATH_INFO"] = matched_path

        return self.wsgi_app(environ, start_response)


app = VercelPathMiddleware(flask_app)
