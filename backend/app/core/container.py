from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from app.core.config import Settings
from app.db.base import Base
from app.db.session import create_engine, create_session_factory
from app.services.audio_service import AudioService
from app.services.generation_service import GenerationService
from app.services.profile_service import ProfileService
from app.services.runtime_service import RuntimeService
from app.services.tts.base import TtsEngine
from app.services.tts.xtts_engine import XttsEngine


class AppContainer:
    def __init__(self, settings: Settings | None = None, tts_engine: TtsEngine | None = None) -> None:
        self.settings = settings or Settings.from_env()
        self.settings.ensure_directories()
        self.engine = create_engine(self.settings.database_url)
        self.session_factory = create_session_factory(self.engine)
        self.executor = ThreadPoolExecutor(max_workers=self.settings.max_generation_workers)
        self.audio_service = AudioService(self.settings)
        self.tts_engine = tts_engine or XttsEngine(self.settings)
        self.profile_service = ProfileService(self.settings, self.audio_service)
        self.generation_service = GenerationService(
            settings=self.settings,
            session_factory=self.session_factory,
            tts_engine=self.tts_engine,
            audio_service=self.audio_service,
            executor=self.executor,
        )
        self.runtime_service = RuntimeService(self.settings, self.tts_engine)

    def startup(self) -> None:
        Base.metadata.create_all(self.engine)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=False)
