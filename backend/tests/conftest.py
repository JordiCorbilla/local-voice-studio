from __future__ import annotations

import array
import io
import wave
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.core.container import AppContainer
from app.main import create_app
from app.services.tts.base import PreparedProfile, SynthesisPayload


class FakeEngine:
    def __init__(self) -> None:
        self.loaded = False

    def load_model(self) -> None:
        self.loaded = True

    def is_ready(self) -> bool:
        return self.loaded

    def prepare_profile(self, profile: PreparedProfile) -> PreparedProfile:
        artifact_path = profile.conditioning_artifact_path
        if artifact_path:
            artifact_path.parent.mkdir(parents=True, exist_ok=True)
            artifact_path.write_bytes(b"cache")
        self.loaded = True
        return profile

    def synthesize(self, profile: PreparedProfile, payload: SynthesisPayload, output_path: Path) -> None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        samples = array.array("h", [0] * 24000)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(samples.tobytes())

    def get_runtime_info(self) -> dict:
        return {
            "engine_name": "fake-engine",
            "model_name": "fake-model",
            "engine_ready": self.loaded,
            "model_loaded": self.loaded,
            "weights_available": True,
            "runtime_device": "cpu",
            "gpu_detected": False,
            "gpu_name": None,
            "python_version": "3.10",
            "torch_version": None,
            "tts_package_installed": False,
            "last_error": None,
            "extras": {},
        }


def make_test_wav_bytes(seconds: int = 3) -> bytes:
    buffer = io.BytesIO()
    samples = array.array("h", [0] * (24000 * seconds))
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(samples.tobytes())
    return buffer.getvalue()


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    data_dir = tmp_path / "data"
    return Settings(
        data_dir=data_dir,
        database_path=data_dir / "app.db",
        profiles_dir=data_dir / "profiles",
        generated_dir=data_dir / "generated",
        cache_dir=data_dir / "cache",
        xtts_cache_dir=data_dir / "cache" / "xtts",
    )


@pytest.fixture()
def container(settings: Settings) -> AppContainer:
    test_container = AppContainer(settings=settings, tts_engine=FakeEngine())
    test_container.startup()
    yield test_container
    test_container.shutdown()


@pytest.fixture()
def client(container: AppContainer) -> TestClient:
    app = create_app(container)
    with TestClient(app) as test_client:
        yield test_client
