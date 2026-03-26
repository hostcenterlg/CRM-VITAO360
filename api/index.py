"""
CRM VITAO360 — Vercel Serverless Entry Point.

Uses Mangum to adapt FastAPI ASGI app to AWS Lambda/Vercel handler.
Database is created in /tmp on cold start and seeded from seed_data.json.
"""
import os
import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Force /tmp for SQLite on Vercel (read-only filesystem)
if os.environ.get("VERCEL"):
    os.environ["DATABASE_URL"] = "sqlite:////tmp/crm_vitao360.db"

# Import after path setup
from mangum import Mangum
from backend.app.main import app

handler = Mangum(app, lifespan="auto")
