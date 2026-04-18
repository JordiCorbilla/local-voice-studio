from __future__ import annotations

import array
import importlib.util
import logging
import sys
import wave
from pathlib import Path
from typing import Any

from app.core.config import Settings
from app.core.errors import AppError
from app.services.tts.base import PreparedProfile, SynthesisPayload
from app.utils.torch_compat import patch_torch_load_for_coqui

logger = logging.getLogger(__name__)


class XttsEngine:
    name = "xtts-v2"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._model = None
        self._torch = None
        self._device = "cpu"
        self._last_error: str | None = None

    def load_model(self) -> None:
        if self._model is not None:
            return
        if importlib.util.find_spec("TTS") is None:
            self._last_error = "Coqui TTS is not installed. Install backend with the [xtts] extra."
            raise AppError(self._last_error, 503, "tts_package_missing")

        try:
            import torch
            from TTS.api import TTS
        except Exception as exc:
            self._last_error = str(exc)
            raise AppError(f"Failed to import XTTS runtime: {exc}", 503, "tts_import_failed")

        self._torch = torch
        patch_torch_load_for_coqui(torch)
        self._device = "cuda" if torch.cuda.is_available() else "cpu"

        try:
            if self.settings.xtts_model_dir:
                self._model = TTS(model_path=str(self.settings.xtts_model_dir), progress_bar=False).to(self._device)
            else:
                self._model = TTS(self.settings.xtts_model_name, progress_bar=False).to(self._device)
            self._last_error = None
        except Exception as exc:
            logger.exception("Failed to load XTTS model")
            self._last_error = str(exc)
            raise AppError(f"Failed to load XTTS model: {exc}", 503, "tts_model_load_failed")

    def is_ready(self) -> bool:
        return self._model is not None and self._last_error is None

    def prepare_profile(self, profile: PreparedProfile) -> PreparedProfile:
        if not profile.reference_paths:
            raise AppError("The selected profile has no reference clips.", 400, "missing_reference_audio")

        artifact_path = profile.conditioning_artifact_path or (
            self.settings.xtts_cache_dir / profile.profile_id / "conditioning.pt"
        )
        artifact_path.parent.mkdir(parents=True, exist_ok=True)

        if self._maybe_prepare_cached_conditioning(profile, artifact_path):
            return PreparedProfile(
                profile_id=profile.profile_id,
                language=profile.language,
                reference_paths=profile.reference_paths,
                primary_reference_path=profile.primary_reference_path,
                conditioning_artifact_path=artifact_path,
                conditioning_fingerprint=profile.conditioning_fingerprint,
            )

        return PreparedProfile(
            profile_id=profile.profile_id,
            language=profile.language,
            reference_paths=profile.reference_paths,
            primary_reference_path=profile.primary_reference_path,
            conditioning_artifact_path=artifact_path if artifact_path.exists() else None,
            conditioning_fingerprint=profile.conditioning_fingerprint,
        )

    def synthesize(self, profile: PreparedProfile, payload: SynthesisPayload, output_path: Path) -> None:
        self.load_model()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._try_cached_inference(profile, payload, output_path):
            self._model.tts_to_file(
                text=payload.text,
                speaker_wav=[str(path) for path in profile.reference_paths],
                language=payload.language,
                file_path=str(output_path),
                **payload.parameters,
            )

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
        if self.settings.xtts_model_dir:
            weights_available = self.settings.xtts_model_dir.exists()
        elif self._model is not None:
            weights_available = True

        return {
            "engine_name": self.name,
            "model_name": self.settings.xtts_model_name,
            "engine_ready": self.is_ready(),
            "model_loaded": self._model is not None,
            "weights_available": weights_available,
            "runtime_device": self._device,
            "gpu_detected": gpu_detected,
            "gpu_name": gpu_name,
            "python_version": sys.version.split()[0],
            "torch_version": torch_version,
            "tts_package_installed": importlib.util.find_spec("TTS") is not None,
            "last_error": self._last_error,
            "extras": {
                "xtts_cache_dir": str(self.settings.xtts_cache_dir),
                "model_dir_override": str(self.settings.xtts_model_dir) if self.settings.xtts_model_dir else None,
            },
        }

    def _maybe_prepare_cached_conditioning(self, profile: PreparedProfile, artifact_path: Path) -> bool:
        try:
            self.load_model()
            model = self._model.synthesizer.tts_model
            if artifact_path.exists():
                data = self._torch.load(str(artifact_path), map_location="cpu")
                if data.get("fingerprint") == profile.conditioning_fingerprint:
                    return True

            latent_output = model.get_conditioning_latents(audio_path=[str(path) for path in profile.reference_paths])
            if isinstance(latent_output, tuple) and len(latent_output) == 2:
                gpt_cond_latent, speaker_embedding = latent_output
            elif isinstance(latent_output, dict):
                gpt_cond_latent = latent_output.get("gpt_cond_latent")
                speaker_embedding = latent_output.get("speaker_embedding")
            else:
                return False

            if gpt_cond_latent is None or speaker_embedding is None:
                return False

            self._torch.save(
                {
                    "fingerprint": profile.conditioning_fingerprint,
                    "gpt_cond_latent": gpt_cond_latent.detach().cpu(),
                    "speaker_embedding": speaker_embedding.detach().cpu(),
                },
                str(artifact_path),
            )
            return True
        except Exception as exc:
            logger.warning("XTTS conditioning cache unavailable: %s", exc)
            return False

    def _try_cached_inference(self, profile: PreparedProfile, payload: SynthesisPayload, output_path: Path) -> bool:
        artifact_path = profile.conditioning_artifact_path
        if not artifact_path or not artifact_path.exists():
            return False
        try:
            self.load_model()
            cache = self._torch.load(str(artifact_path), map_location=self._device)
            if cache.get("fingerprint") != profile.conditioning_fingerprint:
                return False

            model = self._model.synthesizer.tts_model
            waveform = model.inference(
                text=payload.text,
                language=payload.language,
                gpt_cond_latent=cache["gpt_cond_latent"],
                speaker_embedding=cache["speaker_embedding"],
                **payload.parameters,
            )
            wav = waveform["wav"] if isinstance(waveform, dict) else waveform
            self._write_wave(output_path, wav)
            return True
        except Exception as exc:
            logger.warning("Cached XTTS inference failed, falling back to reference audio: %s", exc)
            return False

    def _write_wave(self, output_path: Path, wav: Any) -> None:
        samples = []
        for sample in wav:
            clamped = max(-1.0, min(1.0, float(sample)))
            samples.append(int(clamped * 32767))

        pcm = array.array("h", samples)
        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(pcm.tobytes())
