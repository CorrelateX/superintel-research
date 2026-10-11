"""FastAPI entrypoint for the public research and paper-simulation API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from superintel_research.backend.config import settings
from superintel_research.backend.routes import broker, health, research, safety

app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description=(
        "Research diagnostics and a deterministic paper-execution simulation. "
        "No live broker connectivity is included."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.include_router(health.router)
app.include_router(research.router)
app.include_router(broker.router)
app.include_router(safety.router)

frontend_dir = Path(__file__).resolve().parents[3] / "frontend"
if frontend_dir.is_dir():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="console")
