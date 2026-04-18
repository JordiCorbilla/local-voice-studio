from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ApiModel
from app.schemas.shared import ProfileDefaults


class GenerationRequest(BaseModel):
    profile_id: str
    input_text: str = Field(min_length=1)
    language: str | None = Field(default=None, min_length=2, max_length=16)
    delivery_instructions: str | None = Field(default=None, max_length=500)
    seed: int | None = None
    parameters: ProfileDefaults | None = None


class GenerationRecord(ApiModel):
    id: str
    profile_id: str
    input_text: str
    language: str
    engine_name: str
    delivery_instructions: str | None
    seed: int | None
    parameters: dict[str, Any]
    output_file: str | None
    output_url: str | None
    duration_seconds: float | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
