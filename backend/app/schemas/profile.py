from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.common import ApiModel
from app.schemas.shared import ProfileDefaults


class ReferenceClip(ApiModel):
    id: str
    profile_id: str
    original_filename: str
    mime_type: str
    duration_seconds: float
    sample_rate: int
    channels: int
    is_primary: bool
    created_at: datetime
    original_file: str
    normalized_file: str
    audio_url: str


class ProfileCreate(BaseModel):
    display_name: str = Field(min_length=1, max_length=120)
    notes: str = ""
    language_preference: str = Field(default="en", min_length=2, max_length=16)
    tags: list[str] = Field(default_factory=list)
    avatar_color: str = "#7dd3fc"
    synthesis_defaults: ProfileDefaults = Field(default_factory=ProfileDefaults)


class ProfileUpdate(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=120)
    notes: str | None = None
    language_preference: str | None = Field(default=None, min_length=2, max_length=16)
    tags: list[str] | None = None
    avatar_color: str | None = None
    synthesis_defaults: ProfileDefaults | None = None


class ProfileSummary(ApiModel):
    id: str
    display_name: str
    notes: str
    language_preference: str
    tags: list[str]
    avatar_color: str
    synthesis_defaults: dict[str, Any]
    clip_count: int
    primary_clip_id: str | None
    created_at: datetime
    updated_at: datetime


class ProfileDetail(ProfileSummary):
    clips: list[ReferenceClip]
    recent_generations: list["GenerationRecord"]


from app.schemas.generation import GenerationRecord

ProfileDetail.model_rebuild()
