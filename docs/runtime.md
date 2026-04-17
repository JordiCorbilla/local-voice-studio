# Runtime notes

## XTTS adapter

- The backend lazily loads Coqui XTTS v2 on first synthesis or preparation attempt.
- CUDA is preferred when `torch.cuda.is_available()` is true; otherwise the backend falls back to CPU.
- If `TTS` is not installed, the backend still starts and the diagnostics endpoint reports degraded readiness.

## Conditioning cache

- The backend computes a fingerprint from normalized clip paths, file sizes, and mtimes.
- When XTTS exposes conditioning latents cleanly, the backend stores them in `data/cache/xtts/{profile_id}/conditioning.pt`.
- If cached inference fails or the cache is stale, synthesis falls back to XTTS `speaker_wav` inference using normalized references.

## Audio normalization

- Uploads and recordings are normalized with `ffmpeg` to mono 24kHz PCM16 WAV.
- `ffprobe` extracts duration, sample rate, and channel metadata.
- Clips shorter than 3 seconds are rejected to avoid brittle zero-shot conditioning.

## Diagnostics

- `GET /api/health` reports coarse readiness.
- `GET /api/runtime` reports model configuration, device choice, dependency checks, and active directories.
