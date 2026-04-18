# local-voice-studio

`local-voice-studio` is a local-first voice cloning studio built around a React frontend and a FastAPI backend. It records or uploads reference clips, stores profile metadata in SQLite, keeps audio assets on disk, and runs local XTTS-based synthesis jobs without a cloud service.

## Repository layout

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

## Setup

### Requirements

- Python 3.10+
- Node.js 22+
- FFmpeg and FFprobe on `PATH`
- Optional NVIDIA CUDA setup for faster XTTS inference

### Install

```powershell
.\scripts\setup.ps1
```

The setup script creates `.venv`, installs backend dependencies, and runs `npm.cmd install` in `frontend/`.

### Optional XTTS install

The default setup keeps XTTS optional so the rest of the app can run and test without the heavy runtime. To enable real synthesis:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".\backend[xtts]"
.\.venv\Scripts\python.exe .\scripts\prefetch-model.py
```

If XTTS install pulled `transformers` 5.x, force a compatible 4.x release and rerun the prefetch:

```powershell
.\.venv\Scripts\python.exe -m pip install "transformers>=4.43,<4.47" --upgrade --force-reinstall
.\.venv\Scripts\python.exe -m pip install "numpy==1.22.0" --upgrade --force-reinstall
.\.venv\Scripts\python.exe .\scripts\prefetch-model.py
```

## Run locally

Start the backend:

```powershell
.\scripts\dev-backend.ps1
```

Start the frontend in another terminal:

```powershell
.\scripts\dev-frontend.ps1
```

Open `http://localhost:5173`.

## Environment variables

- `LVS_CORS_ORIGIN`
- `LVS_DATA_DIR`
- `LVS_DATABASE_PATH`
- `LVS_PROFILES_DIR`
- `LVS_GENERATED_DIR`
- `LVS_CACHE_DIR`
- `LVS_XTTS_CACHE_DIR`
- `LVS_XTTS_MODEL_NAME`
- `LVS_XTTS_MODEL_DIR`
- `LVS_FFMPEG_BIN`
- `LVS_FFPROBE_BIN`
- `LVS_MAX_GENERATION_WORKERS`

## Data layout

- `data/app.db`: SQLite metadata
- `data/profiles/{profile_id}/clips/{clip_id}/original{ext}`: original reference upload
- `data/profiles/{profile_id}/clips/{clip_id}/normalized.wav`: normalized internal reference
- `data/generated/{generation_id}.wav`: generated outputs
- `data/cache/xtts/{profile_id}/conditioning.pt`: cached conditioning artifacts when available

## API summary

- `GET/POST /api/profiles`
- `GET/PATCH/DELETE /api/profiles/{id}`
- `GET /api/profiles/{id}/clips`
- `POST /api/profiles/{id}/clips/upload`
- `POST /api/profiles/{id}/clips/recording`
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
..\.venv\Scripts\python.exe -m pytest
```

Frontend:

```powershell
Set-Location .\frontend
npm.cmd run test
```

## Troubleshooting

- If `npm` fails in PowerShell due to execution policy, use `npm.cmd`.
- If uploads fail, verify both `ffmpeg` and `ffprobe` are available on `PATH`.
- If XTTS is unavailable in diagnostics, install the backend `xtts` extra and prefetch the model.
- If XTTS fails with `BeamSearchScorer` import errors, your `transformers` install is too new; reinstall `transformers>=4.43,<4.47`.
- If XTTS complains about `TorchCodec is required for load_with_torchcodec`, update to the latest project code. The backend now patches XTTS to read the app's normalized WAV references without requiring `torchcodec`.
- CPU synthesis works but will be substantially slower than CUDA on long inputs.

## Privacy

All profile metadata, reference clips, generated outputs, and cache artifacts stay on the local filesystem. There is no cloud sync, auth layer, or remote inference service in this repository.
