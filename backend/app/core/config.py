from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Settings:
    app_name: str = "Local Voice Studio"
    api_prefix: str = "/api"
    cors_origin: str = "http://localhost:5173"
    data_dir: Path = Path("data")
    database_path: Path = Path("data/app.db")
    profiles_dir: Path = Path("data/profiles")
    generated_dir: Path = Path("data/generated")
    cache_dir: Path = Path("data/cache")
    xtts_cache_dir: Path = Path("data/cache/xtts")
    xtts_model_name: str = "tts_models/multilingual/multi-dataset/xtts_v2"
    xtts_model_dir: Path | None = None
    ffmpeg_bin: str = "ffmpeg"
    ffprobe_bin: str = "ffprobe"
    max_generation_workers: int = 2

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.database_path.as_posix()}"

    @classmethod
    def from_env(cls) -> "Settings":
        xtts_model_dir = os.getenv("LVS_XTTS_MODEL_DIR")
        return cls(
            cors_origin=os.getenv("LVS_CORS_ORIGIN", "http://localhost:5173"),
            data_dir=Path(os.getenv("LVS_DATA_DIR", "data")),
            database_path=Path(os.getenv("LVS_DATABASE_PATH", "data/app.db")),
            profiles_dir=Path(os.getenv("LVS_PROFILES_DIR", "data/profiles")),
            generated_dir=Path(os.getenv("LVS_GENERATED_DIR", "data/generated")),
            cache_dir=Path(os.getenv("LVS_CACHE_DIR", "data/cache")),
            xtts_cache_dir=Path(os.getenv("LVS_XTTS_CACHE_DIR", "data/cache/xtts")),
            xtts_model_name=os.getenv(
                "LVS_XTTS_MODEL_NAME",
                "tts_models/multilingual/multi-dataset/xtts_v2",
            ),
            xtts_model_dir=Path(xtts_model_dir) if xtts_model_dir else None,
            ffmpeg_bin=os.getenv("LVS_FFMPEG_BIN", "ffmpeg"),
            ffprobe_bin=os.getenv("LVS_FFPROBE_BIN", "ffprobe"),
            max_generation_workers=int(os.getenv("LVS_MAX_GENERATION_WORKERS", "2")),
        )

    def ensure_directories(self) -> None:
        for directory in (
            self.data_dir,
            self.profiles_dir,
            self.generated_dir,
            self.cache_dir,
            self.xtts_cache_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
