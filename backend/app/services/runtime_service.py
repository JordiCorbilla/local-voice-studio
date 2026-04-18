from __future__ import annotations

from app.core.config import Settings
from app.services.transcription_service import TranscriptionService
from app.services.tts.base import TtsEngine


class RuntimeService:
    def __init__(self, settings: Settings, tts_engine: TtsEngine, transcription_service: TranscriptionService) -> None:
        self.settings = settings
        self.tts_engine = tts_engine
        self.transcription_service = transcription_service

    def health(self, ffmpeg_available: bool) -> dict:
        return {
            "status": "ok",
            "database": "ok",
            "ffmpeg_available": ffmpeg_available,
            "engine_ready": self.tts_engine.is_ready(),
        }

    def runtime_info(self, *, ffmpeg_available: bool, ffprobe_available: bool) -> dict:
        info = self.tts_engine.get_runtime_info()
        info["ffmpeg_available"] = ffmpeg_available
        info["ffprobe_available"] = ffprobe_available
        transcription = self.transcription_service.runtime_info()
        info["transcription_available"] = transcription["available"]
        info["transcription_model"] = transcription["model_name"]
        info["directories"] = {
            "data": str(self.settings.data_dir),
            "database": str(self.settings.database_path),
            "profiles": str(self.settings.profiles_dir),
            "generated": str(self.settings.generated_dir),
            "cache": str(self.settings.cache_dir),
            "xtts_cache": str(self.settings.xtts_cache_dir),
            "qwen_cache": str(self.settings.qwen_cache_dir),
        }
        return info
