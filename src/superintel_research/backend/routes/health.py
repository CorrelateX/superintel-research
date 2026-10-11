"""Health check endpoints."""

from __future__ import annotations

import os
from fastapi import APIRouter
from superintel_research.backend.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check():
    db_status = "unconnected"
    dsn = settings.database_url
    if dsn:
        try:
            import psycopg
            with psycopg.connect(dsn, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1")
                    db_status = "connected"
        except Exception as exc:
            db_status = f"error: {exc}"

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "database": db_status,
        "kill_switch_active": os.environ.get("KILL_SWITCH", "0").lower() in {"1", "true", "yes"},
    }
