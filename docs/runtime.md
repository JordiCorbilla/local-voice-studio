# Runtime notes

## XTTS adapter

- The backend lazily loads Coqui XTTS v2 on first synthesis or preparation attempt.
- CUDA is preferred when `torch.cuda.is_available()` is true; otherwise the backend falls back to CPU.
- If `TTS` is not installed, the backend still starts and the diagnostics endpoint reports degraded readiness.

## Qwen3 adapter

- The backend can switch to `Qwen3-TTS` with `LVS_TTS_ENGINE=qwen3`.
- Qwen3 cloning uses the selected primary clip plus its saved transcript, so the profile workflow now treats the transcript as part of the conditioning input.
- Prompt caching is opportunistic. If prompt serialization works, the backend stores a reusable voice-clone prompt under `data/cache/qwen3/{profile_id}/voice_clone_prompt.pkl`; otherwise it rebuilds the prompt on demand.

## Conditioning cache

- The backend computes a fingerprint from normalized clip paths, file sizes, and mtimes.
- When XTTS exposes conditioning latents cleanly, the backend stores them in `data/cache/xtts/{profile_id}/conditioning.pt`.
- If cached inference fails or the cache is stale, synthesis falls back to XTTS `speaker_wav` inference using normalized references.
- The fingerprint now also includes the primary clip transcript so transcript edits invalidate cached prompts.

## Audio normalization

- Uploads and recordings are normalized with `ffmpeg` to mono 24kHz PCM16 WAV.
- `ffprobe` extracts duration, sample rate, and channel metadata.
- Clips shorter than 3 seconds are rejected to avoid brittle zero-shot conditioning.

## Diagnostics

- `GET /api/health` reports coarse readiness.
- `GET /api/runtime` reports the active engine, model configuration, device choice, dependency checks, transcription availability, and active directories.
