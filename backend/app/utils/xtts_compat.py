from __future__ import annotations

from typing import Any


def patch_xtts_audio_loader() -> None:
    """Patch Coqui XTTS to load normalized WAVs without torchcodec."""
    try:
        import soundfile as sf
        import torch
        import torchaudio
        from TTS.tts.models import xtts as xtts_module
    except Exception:
        return

    if getattr(xtts_module.load_audio, "__lvs_patched__", False):
        return

    def load_audio(audiopath: str, sampling_rate: int):
        audio, source_rate = sf.read(audiopath, dtype="float32", always_2d=True)
        waveform = torch.from_numpy(audio.T)
        if waveform.size(0) != 1:
            waveform = waveform.mean(dim=0, keepdim=True)
        if source_rate != sampling_rate:
            waveform = torchaudio.functional.resample(waveform, source_rate, sampling_rate)
        return waveform

    load_audio.__lvs_patched__ = True  # type: ignore[attr-defined]
    xtts_module.load_audio = load_audio
