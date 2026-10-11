"""Backend service configuration."""

from __future__ import annotations

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "SuperIntel Research Simulation API"
    version: str = "0.1.0"
    environment: str = os.environ.get("ENVIRONMENT", "development")
    log_level: str = os.environ.get("LOG_LEVEL", "INFO")
    database_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql://superintel_research:superintel_research@127.0.0.1:5433/superintel_research",
    )
settings = Settings()
