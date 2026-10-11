"""Process-local paper-simulation kill switch routes."""

from __future__ import annotations

import os
from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/simulation/safety", tags=["Paper Simulation"])


class KillSwitchBody(BaseModel):
    active: bool = Field(..., json_schema_extra={"example": True})


@router.get("/kill-switch")
def get_kill_switch_status():
    active = os.environ.get("KILL_SWITCH", "0").lower() in {"1", "true", "yes"}
    return {"kill_switch_active": active}


@router.post("/kill-switch")
def toggle_kill_switch(body: KillSwitchBody):
    os.environ["KILL_SWITCH"] = "1" if body.active else "0"
    return {
        "kill_switch_active": body.active,
        "message": (
            "Paper simulation halted."
            if body.active
            else "Paper simulation enabled."
        ),
    }
