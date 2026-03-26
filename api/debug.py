"""Debug handler — Vercel Python format."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        info = {
            "status": "ok",
            "python": sys.version,
            "cwd": os.getcwd(),
            "root": root,
            "backend_exists": os.path.isdir(os.path.join(root, "backend")),
            "data_exists": os.path.isdir(os.path.join(root, "data")),
        }

        # Try imports
        try:
            if root not in sys.path:
                sys.path.insert(0, root)
            os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/crm.db")
            os.environ.setdefault("JWT_SECRET", "test")

            import fastapi
            info["fastapi"] = fastapi.__version__

            import sqlalchemy
            info["sqlalchemy"] = sqlalchemy.__version__

            import mangum
            info["mangum"] = "ok"

            from backend.app.main import app
            info["app"] = app.title
        except Exception as e:
            import traceback
            info["error"] = str(e)
            info["traceback"] = traceback.format_exc()

        body = json.dumps(info, indent=2).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)
