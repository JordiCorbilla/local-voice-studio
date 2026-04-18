from __future__ import annotations

import array
import importlib.util
import inspect
import logging
import pickle
import sys
import wave
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.services.tts.base import PreparedProfile, SynthesisPayload

logger = logging.getLogger(__name__)


class Qwen3Engine:
    name = "qwen3-tts"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._last_error: str | None = None
        self._prompt_cache: dict[str, Any] = {}

    def load_model(self) -> None:
        if self._model is not None:
            return
        if importlib.util.find_spec("qwen_tts") is None:
            self._last_error = "Qwen3-TTS is not installed. Install backend with the [qwen] extra."
            raise AppError(self._last_error, 503, "tts_package_missing")

        try:
            import torch
            from qwen_tts import Qwen3TTSModel
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Failed to import Qwen3-TTS runtime: {exc}", 503, "tts_import_failed")

        self._torch = torch
        self._device = "cuda:0" if torch.cuda.is_available() else "cpu"
        dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        load_target = str(self.settings.qwen_model_dir) if self.settings.qwen_model_dir else self.settings.qwen_model_name
        kwargs: dict[str, Any] = {
            "device_map": self._device,
            "dtype": dtype,
        }
        if torch.cuda.is_available():
            kwargs["attn_implementation"] = "flash_attention_2"
        try:
            self._model = Qwen3TTSModel.from_pretrained(load_target, **kwargs)
            self._last_error = None
        except Exception as exc:
            logger.exception("Failed to load Qwen3-TTS model")
            self._last_error = str(exc)
            raise AppError(f"Failed to load Qwen3-TTS model: {exc}", 503, "tts_model_load_failed")

    def is_ready(self) -> bool:
        return self._model is not None and self._last_error is None

    def prepare_profile(self, profile: PreparedProfile) -> PreparedProfile:
        if not profile.reference_paths:
            raise AppError("The selected profile has no reference clips.", 400, "missing_reference_audio")
        if not (profile.primary_reference_text or "").strip():
            raise AppError(
                "The selected primary clip needs a reference transcript for Qwen3 voice cloning.",
                400,
                "missing_reference_transcript",
            )

        artifact_path = profile.conditioning_artifact_path or (
            self.settings.qwen_cache_dir / profile.profile_id / "voice_clone_prompt.pkl"
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = self._load_cached_prompt(artifact_path, profile.conditioning_fingerprint)
        if prompt is None:
            prompt = self._create_prompt(profile)
            self._store_prompt(profile, artifact_path, prompt)
        return PreparedProfile(
            profile_id=profile.profile_id,
            language=profile.language,
            reference_paths=profile.reference_paths,
            primary_reference_path=profile.primary_reference_path,
            primary_reference_text=profile.primary_reference_text,
            conditioning_artifact_path=artifact_path if artifact_path.exists() else None,
            conditioning_fingerprint=profile.conditioning_fingerprint,
        )

    def synthesize(self, profile: PreparedProfile, payload: SynthesisPayload, output_path: Path) -> None:
        self.load_model()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        prompt = None
        if profile.conditioning_artifact_path:
            prompt = self._load_cached_prompt(profile.conditioning_artifact_path, profile.conditioning_fingerprint)
        if prompt is None:
            prompt = self._create_prompt(profile)
            if profile.conditioning_artifact_path:
                self._store_prompt(profile, profile.conditioning_artifact_path, prompt)

        if payload.seed is not None and self._torch is not None:
            self._torch.manual_seed(payload.seed)
            if self._torch.cuda.is_available():
                self._torch.cuda.manual_seed_all(payload.seed)

        language = _normalize_language(payload.language)
        kwargs = self._filter_generation_parameters(payload.parameters)
        clone_method = self._model.generate_voice_clone
        signature = inspect.signature(clone_method)
        if payload.delivery_instructions and "instruct" in signature.parameters:
            kwargs["instruct"] = payload.delivery_instructions

        if prompt is not None:
            wavs, sample_rate = clone_method(
                text=payload.text,
                language=language,
                voice_clone_prompt=prompt,
                **kwargs,
            )
        else:
            wavs, sample_rate = clone_method(
                text=payload.text,
                language=language,
                ref_audio=str(profile.primary_reference_path),
                ref_text=profile.primary_reference_text,
                **kwargs,
            )
        wav = wavs[0] if isinstance(wavs, (list, tuple)) else wavs
        self._write_wave(output_path, wav, sample_rate)

    def get_runtime_info(self) -> dict[str, Any]:
        gpu_detected = False
        gpu_name = None
        torch_version = None
        if importlib.util.find_spec("torch") is not None:
            import torch

            torch_version = getattr(torch, "__version__", None)
            gpu_detected = bool(torch.cuda.is_available())
            if gpu_detected:
                gpu_name = torch.cuda.get_device_name(0)

        weights_available = False
        if self.settings.qwen_model_dir:
            weights_available = self.settings.qwen_model_dir.exists()
        elif self._model is not None:
            weights_available = True

        return {
            "engine_name": self.name,
            "active_engine": self.settings.tts_engine,
            "model_name": self.settings.qwen_model_name,
            "engine_ready": self.is_ready(),
            "model_loaded": self._model is not None,
            "weights_available": weights_available,
            "runtime_device": self._device,
            "gpu_detected": gpu_detected,
            "gpu_name": gpu_name,
            "python_version": sys.version.split()[0],
            "torch_version": torch_version,
            "tts_package_installed": importlib.util.find_spec("qwen_tts") is not None,
            "last_error": self._last_error,
            "extras": {
                "qwen_cache_dir": str(self.settings.qwen_cache_dir),
                "model_dir_override": str(self.settings.qwen_model_dir) if self.settings.qwen_model_dir else None,
            },
        }

    def _create_prompt(self, profile: PreparedProfile) -> Any:
        self.load_model()
        return self._model.create_voice_clone_prompt(
            ref_audio=str(profile.primary_reference_path),
            ref_text=profile.primary_reference_text,
            x_vector_only_mode=False,
        )

    def _load_cached_prompt(self, artifact_path: Path, fingerprint: str) -> Any | None:
        cache_key = f"{artifact_path}:{fingerprint}"
        if cache_key in self._prompt_cache:
            return self._prompt_cache[cache_key]
        if not artifact_path.exists():
            return None
        try:
            with artifact_path.open("rb") as handle:
                payload = pickle.load(handle)
            if payload.get("fingerprint") != fingerprint:
                return None
            prompt = payload.get("prompt")
            self._prompt_cache[cache_key] = prompt
            return prompt
        except Exception as exc:
            logger.warning("Unable to load Qwen3 prompt cache: %s", exc)
            return None

    def _store_prompt(self, profile: PreparedProfile, artifact_path: Path, prompt: Any) -> None:
        cache_key = f"{artifact_path}:{profile.conditioning_fingerprint}"
        self._prompt_cache[cache_key] = prompt
        try:
            with artifact_path.open("wb") as handle:
                pickle.dump({"fingerprint": profile.conditioning_fingerprint, "prompt": prompt}, handle)
        except Exception as exc:
            logger.warning("Unable to persist Qwen3 prompt cache: %s", exc)

    def _filter_generation_parameters(self, parameters: dict[str, Any]) -> dict[str, Any]:
        allowed = {"temperature", "top_k", "top_p", "length_penalty", "repetition_penalty"}
        return {key: value for key, value in parameters.items() if key in allowed}

    def _write_wave(self, output_path: Path, wav: Any, sample_rate: int) -> None:
        samples = []
        for sample in wav:
            clamped = max(-1.0, min(1.0, float(sample)))
            samples.append(int(clamped * 32767))

        pcm = array.array("h", samples)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm.tobytes())


def _normalize_language(language: str) -> str:
    mapping = {
        "en": "English",
        "en-us": "English",
        "en-gb": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "ru": "Russian",
        "ja": "Japanese",
        "ko": "Korean",
        "zh": "Chinese",
        "zh-cn": "Chinese",
    }
    return mapping.get(language.lower(), language)
