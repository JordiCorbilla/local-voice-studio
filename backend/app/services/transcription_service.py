from __future__ import annotations

import importlib.util
import logging
from pathlib import Path

from app.core.config import Settings
from app.core.errors import AppError

logger = logging.getLogger(__name__)


class TranscriptionService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._last_error: str | None = None

    def is_available(self) -> bool:
        return importlib.util.find_spec("faster_whisper") is not None

    def transcribe(self, audio_path: Path, *, language: str | None = None) -> str:
        if not self.is_available():
            raise AppError(
                "Local transcription is unavailable. Install backend with the [transcription] extra.",
                503,
                "transcription_unavailable",
            )
        model = self._load_model()
        try:
            segments, _ = model.transcribe(
                str(audio_path),
                language=_normalize_whisper_language(language),
                vad_filter=True,
            )
            transcript = " ".join(segment.text.strip() for segment in segments).strip()
            if not transcript:
                raise AppError("No transcript could be extracted from the reference clip.", 400, "empty_transcript")
            self._last_error = None
            return transcript
        except AppError:
            raise
        except Exception as exc:
            logger.exception("Reference clip transcription failed")
            self._last_error = str(exc)
            raise AppError(f"Transcription failed: {exc}", 500, "transcription_failed")

    def runtime_info(self) -> dict[str, str | bool | None]:
        return {
            "available": self.is_available(),
            "model_name": self.settings.whisper_model_name,
            "last_error": self._last_error,
        }

    def _load_model(self):
        if self._model is not None:
            return self._model
        try:
            from faster_whisper import WhisperModel
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Failed to import local transcription runtime: {exc}", 503, "transcription_import_failed")

        device = self.settings.whisper_device
        if device == "auto":
            device = "cuda" if _cuda_available() else "cpu"
        compute_type = self.settings.whisper_compute_type
        if compute_type == "auto":
            compute_type = "float16" if device == "cuda" else "int8"
        self._model = WhisperModel(self.settings.whisper_model_name, device=device, compute_type=compute_type)
        return self._model


def _normalize_whisper_language(language: str | None) -> str | None:
    if not language:
        return None
    language = language.lower()
    mapping = {
        "en": "en",
        "en-us": "en",
        "en-gb": "en",
        "es": "es",
        "fr": "fr",
        "de": "de",
        "it": "it",
        "pt": "pt",
        "ru": "ru",
        "ja": "ja",
        "ko": "ko",
        "zh": "zh",
        "zh-cn": "zh",
    }
    return mapping.get(language, language)


def _cuda_available() -> bool:
    if importlib.util.find_spec("torch") is None:
        return False
    import torch

    return bool(torch.cuda.is_available())
