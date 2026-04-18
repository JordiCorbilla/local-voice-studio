from __future__ import annotations

from typing import Any

from app.schemas.common import ApiModel


class HealthStatus(ApiModel):
    status: str
    database: str
    ffmpeg_available: bool
    engine_ready: bool


class RuntimeInfo(ApiModel):
    model_name: str
    engine_name: str
    active_engine: str
    engine_ready: bool
    model_loaded: bool
    weights_available: bool
    runtime_device: str
    gpu_detected: bool
    gpu_name: str | None
    python_version: str
    torch_version: str | None
    tts_package_installed: bool
    ffmpeg_available: bool
    ffprobe_available: bool
    directories: dict[str, str]
    last_error: str | None
    transcription_available: bool | None = None
    transcription_model: str | None = None
    extras: dict[str, Any]
