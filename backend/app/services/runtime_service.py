from __future__ import annotations

from app.core.config import Settings
from app.services.tts.base import TtsEngine


class RuntimeService:
    def __init__(self, settings: Settings, tts_engine: TtsEngine) -> None:
        self.settings = settings
        self.tts_engine = tts_engine

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
        info["directories"] = {
            "data": str(self.settings.data_dir),
            "database": str(self.settings.database_path),
            "profiles": str(self.settings.profiles_dir),
            "generated": str(self.settings.generated_dir),
            "cache": str(self.settings.cache_dir),
            "xtts_cache": str(self.settings.xtts_cache_dir),
        }
        return info
