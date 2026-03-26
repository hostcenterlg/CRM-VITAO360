"""Debug handler to diagnose import errors on Vercel."""
import json
import os
import sys
import traceback


def handler(event, context):
    """Return diagnostic info about the serverless environment."""
    info = {
        "python_version": sys.version,
        "cwd": os.getcwd(),
        "sys_path": sys.path[:5],
        "env_keys": sorted([k for k in os.environ if not k.startswith("AWS")])[:20],
        "vercel_env": os.environ.get("VERCEL", "NOT SET"),
    }

    # Try importing backend
    try:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if root not in sys.path:
            sys.path.insert(0, root)

        # Check backend dir exists
        backend_dir = os.path.join(root, "backend")
        info["backend_exists"] = os.path.isdir(backend_dir)
        info["backend_app_exists"] = os.path.isdir(os.path.join(backend_dir, "app"))

        # List files in backend/app
        app_dir = os.path.join(backend_dir, "app")
        if os.path.isdir(app_dir):
            info["backend_app_files"] = os.listdir(app_dir)[:20]

        # Try imports one by one
        imports_ok = []
        imports_fail = []

        for mod in [
            "backend",
            "backend.app",
            "backend.app.database",
            "backend.app.main",
            "mangum",
            "fastapi",
            "sqlalchemy",
            "pydantic",
            "jose",
            "bcrypt",
        ]:
            try:
                __import__(mod)
                imports_ok.append(mod)
            except Exception as e:
                imports_fail.append(f"{mod}: {e}")

        info["imports_ok"] = imports_ok
        info["imports_fail"] = imports_fail

    except Exception as e:
        info["error"] = str(e)
        info["traceback"] = traceback.format_exc()

    body = json.dumps(info, indent=2, default=str)

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": body,
    }
