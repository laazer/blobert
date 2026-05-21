"""Health probe response model (M902-25 pilot)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    """Liveness probe for the asset editor API."""

    model_config = ConfigDict(extra="forbid", ser_json_exclude_none=True)

    status: Literal["ok"] = Field(..., description="Health status; only ok is defined.")
