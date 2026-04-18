from __future__ import annotations

from app.core.config import Settings
from app.core.errors import AppError
from app.services.tts.base import TtsEngine
from app.services.tts.qwen3_engine import Qwen3Engine
from app.services.tts.xtts_engine import XttsEngine


def create_tts_engine(settings: Settings) -> TtsEngine:
    engine_name = settings.tts_engine.lower()
    if engine_name == "xtts":
        return XttsEngine(settings)
    if engine_name in {"qwen", "qwen3", "qwen3-tts"}:
        return Qwen3Engine(settings)
    raise AppError(f"Unsupported TTS engine '{settings.tts_engine}'.", 500, "unsupported_tts_engine")
