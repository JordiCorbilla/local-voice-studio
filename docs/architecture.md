# Architecture

`local-voice-studio` is split into a React/Vite frontend and a FastAPI backend.

## Backend

- Routes are thin and delegate to services.
- Services coordinate repositories, audio normalization, file lifecycle, and TTS orchestration.
- Metadata lives in SQLite.
- Audio, generated WAV files, and conditioning cache artifacts live under `data/`.
- `TtsEngine` is the adapter boundary; `XttsEngine` and `Qwen3Engine` sit behind the same generation service.
- Reference clips now persist an optional `reference_text` transcript so transcript-aware engines can reuse the primary clip without re-entering metadata each run.
- A lightweight local transcription service can populate clip transcripts when the optional backend transcription extra is installed.

## Frontend

- React Router provides the desktop-style workspace navigation.
- TanStack Query manages server state, polling, and cache invalidation.
- Recording is isolated behind a `useRecorder` hook using `MediaRecorder`.
- Feature folders keep profile, generation, history, and diagnostics concerns separated.

## Job model

- Generation requests create a SQLite history row immediately with `queued` status.
- Background worker threads update jobs to `running`, `completed`, or `failed`.
- The frontend polls a single active generation every 2 seconds until terminal state.
