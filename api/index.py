"""
CRM VITAO360 — Vercel Serverless Entry Point.
"""
import os
import sys
from pathlib import Path

# Ensure project root is in sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Always use /tmp for SQLite on Vercel (filesystem is read-only except /tmp)
os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/crm_vitao360.db")
os.environ.setdefault("JWT_SECRET", "vitao360-vercel-secret-2026")

from mangum import Mangum  # noqa: E402
from backend.app.main import app  # noqa: E402

handler = Mangum(app, lifespan="auto")
