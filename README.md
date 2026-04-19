# local-voice-studio

`local-voice-studio` is a local-first voice cloning studio built with React, FastAPI, SQLite, and local model runtimes. It records or uploads reference clips, stores profile metadata locally, keeps generated audio on disk, and can run local TTS without a cloud service.

The app supports two local TTS paths:

- `qwen3`: recommended for closer voice similarity because it uses reference audio plus the exact reference transcript.
- `xtts`: Coqui XTTS v2 fallback/baseline. It is easier to run in some environments but was less faithful for this project.

## Repository Layout

```text
.
|-- backend
|-- data
|   |-- cache
|   |-- generated
|   `-- profiles
|-- docs
|-- frontend
`-- scripts
```

## Requirements

- Windows PowerShell
- Python 3.10+ for the base app and XTTS path
- Python 3.12 is recommended by the upstream Qwen3-TTS docs
- Node.js 22+
- FFmpeg and FFprobe on `PATH`
- Optional NVIDIA CUDA runtime for faster generation

## From Scratch Setup

Run setup first from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

This creates `.venv`, installs backend dev dependencies, and installs frontend dependencies.

If you prefer manual setup:

```powershell
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -e ".\backend[dev]"
npm.cmd --prefix .\frontend install
```

## Recommended Run: Qwen3-TTS

Install the Qwen and local transcription extras:

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".\backend[qwen,transcription]"
```

Start the backend in terminal 1:

```powershell
$env:LVS_TTS_ENGINE = "qwen3"
powershell -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1
```

Start the frontend in terminal 2:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1
```

Open:

```text
http://localhost:5173
```

### If Port 8000 Is Already Busy

Voicebox or another local app may already use `8000`. Use `8010` instead.

Terminal 1:

```powershell
$env:LVS_TTS_ENGINE = "qwen3"
$env:LVS_BACKEND_PORT = "8010"
powershell -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1
```

Terminal 2:

```powershell
$env:VITE_API_TARGET = "http://127.0.0.1:8010"
powershell -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1
```

## Using Qwen3 Voice Cloning

Qwen3 requires the transcript of the selected primary reference clip.

1. Create a profile.
2. Upload or record one clean reference clip.
3. Mark the best clip as `Primary`.
4. Paste the exact words spoken in that clip into `Reference transcript`.
5. Click `Save transcript`.
6. Go to `Generate`.
7. Enter text and optional delivery instructions.
8. Click `Generate audio`.

You can also click `Transcribe locally` on a reference clip if the `transcription` extra is installed. The button shows a spinner while transcription is running.

## Optional Run: XTTS v2

Install XTTS:

```powershell
& .\.venv\Scripts\python.exe -m pip install -e ".\backend[xtts]"
```

Prefetch the XTTS model:

```powershell
& .\.venv\Scripts\python.exe .\scripts\prefetch-model.py
```

Start the backend:

```powershell
$env:LVS_TTS_ENGINE = "xtts"
powershell -ExecutionPolicy Bypass -File .\scripts\dev-backend.ps1
```

Start the frontend:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\dev-frontend.ps1
```

Important: `scripts\prefetch-model.py` is only for XTTS. It is not needed for Qwen3.

## Common PowerShell Notes

If PowerShell blocks `.ps1` scripts, use the one-command bypass:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\setup.ps1
```

Or allow scripts only for the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

Activating the venv is optional because the documented commands call `.venv\Scripts\python.exe` directly.

## Environment Variables

- `LVS_TTS_ENGINE`: `qwen3` or `xtts`
- `LVS_BACKEND_PORT`: backend dev port used by `scripts/dev-backend.ps1`; defaults to `8000`
- `VITE_API_TARGET`: frontend dev proxy target; defaults to `http://127.0.0.1:8000`
- `LVS_CORS_ORIGIN`
- `LVS_DATA_DIR`
- `LVS_DATABASE_PATH`
- `LVS_PROFILES_DIR`
- `LVS_GENERATED_DIR`
- `LVS_CACHE_DIR`
- `LVS_XTTS_CACHE_DIR`
- `LVS_QWEN_CACHE_DIR`
- `LVS_XTTS_MODEL_NAME`
- `LVS_XTTS_MODEL_DIR`
- `LVS_QWEN_MODEL_NAME`
- `LVS_QWEN_MODEL_DIR`
- `LVS_WHISPER_MODEL_NAME`
- `LVS_WHISPER_DEVICE`
- `LVS_WHISPER_COMPUTE_TYPE`
- `LVS_FFMPEG_BIN`
- `LVS_FFPROBE_BIN`
- `LVS_MAX_GENERATION_WORKERS`

## Data Layout

- `data/app.db`: SQLite metadata
- `data/profiles/{profile_id}/clips/{clip_id}/original{ext}`: original reference upload
- `data/profiles/{profile_id}/clips/{clip_id}/normalized.wav`: normalized internal reference
- `data/generated/{generation_id}.wav`: generated outputs
- `data/cache/xtts/{profile_id}/conditioning.pt`: cached XTTS conditioning artifacts when available
- `data/cache/qwen3/{profile_id}/voice_clone_prompt.pkl`: cached Qwen3 voice-clone prompt when available

## API Summary

- `GET/POST /api/profiles`
- `GET/PATCH/DELETE /api/profiles/{id}`
- `GET /api/profiles/{id}/clips`
- `POST /api/profiles/{id}/clips/upload`
- `POST /api/profiles/{id}/clips/recording`
- `PATCH /api/profiles/{id}/clips/{clip_id}`
- `POST /api/profiles/{id}/clips/{clip_id}/transcribe`
- `DELETE /api/profiles/{id}/clips/{clip_id}`
- `POST /api/profiles/{id}/clips/{clip_id}/set-primary`
- `GET/POST /api/generations`
- `GET/DELETE /api/generations/{id}`
- `GET /api/files/generated/{filename}`
- `GET /api/files/reference/{relative_path}`
- `GET /api/health`
- `GET /api/runtime`

## Testing

Backend:

```powershell
Set-Location .\backend
& ..\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
Set-Location .\frontend
npm.cmd run test
```

Build frontend:

```powershell
npm.cmd --prefix .\frontend run build
```

## Troubleshooting

- If `8000` is unavailable, set `LVS_BACKEND_PORT` and `VITE_API_TARGET` as shown above.
- If uploads fail, verify `ffmpeg` and `ffprobe` are available on `PATH`.
- If Qwen3 generation says a transcript is missing, open the selected profile and save `Reference transcript` for the primary clip.
- If Qwen3 logs `flash-attn is not installed`, generation can still work. Flash Attention is an optional speed optimization, mostly relevant on CUDA-capable NVIDIA setups.
- If Qwen3 logs that `sox` could not be found, generation can still work if the current path does not require SoX. Install SoX only if generation/transcription later fails with a SoX-related error.
- If local transcription does nothing for a while, wait for the spinner; the first run may download/load the Whisper model.
- If local transcription is unavailable, install `backend[transcription]` or paste the transcript manually.
- If XTTS fails with `BeamSearchScorer` import errors, reinstall `transformers>=4.43,<4.47`.
- If XTTS complains about `TorchCodec`, update to the latest project code. The backend patches XTTS to read normalized WAV references without requiring `torchcodec`.
- CPU synthesis works but can be much slower than CUDA.

## Privacy

All profile metadata, reference clips, transcripts, generated outputs, and cache artifacts stay on the local filesystem. There is no cloud sync, authentication layer, or remote inference service in this repository.
