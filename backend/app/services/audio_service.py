from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from app.core.config import Settings
from app.core.errors import AppError
from app.utils.files import safe_rmtree, safe_unlink


@dataclass(slots=True)
class AudioMetadata:
    duration_seconds: float
    sample_rate: int
    channels: int


@dataclass(slots=True)
class StoredClip:
    clip_id: str
    original_path: Path
    normalized_path: Path
    original_filename: str
    mime_type: str
    metadata: AudioMetadata


class AudioService:
    allowed_extensions = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm"}

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def store_reference_audio(
        self,
        *,
        profile_id: str,
        filename: str,
        content_type: str,
        payload: bytes,
    ) -> StoredClip:
        extension = Path(filename).suffix.lower()
        if extension not in self.allowed_extensions:
            raise AppError("Unsupported audio file type.", 400, "unsupported_audio_type")
        if not payload:
            raise AppError("Uploaded audio file is empty.", 400, "empty_audio")

        clip_id = str(uuid4())
        clip_dir = self.settings.profiles_dir / profile_id / "clips" / clip_id
        clip_dir.mkdir(parents=True, exist_ok=True)

        original_path = clip_dir / f"original{extension}"
        original_path.write_bytes(payload)
        normalized_path = clip_dir / "normalized.wav"

        try:
            self._normalize_audio(original_path, normalized_path)
            metadata = self._probe_audio(normalized_path)
        except subprocess.CalledProcessError as exc:
            safe_rmtree(clip_dir)
            stderr = exc.stderr.decode("utf-8", errors="ignore") if exc.stderr else ""
            raise AppError(f"Unable to read audio file. {stderr.strip()}".strip(), 400, "invalid_audio")

        if metadata.duration_seconds < 3.0:
            safe_rmtree(clip_dir)
            raise AppError("Reference audio must be at least 3 seconds long.", 400, "audio_too_short")

        return StoredClip(
            clip_id=clip_id,
            original_path=original_path,
            normalized_path=normalized_path,
            original_filename=filename,
            mime_type=content_type or "application/octet-stream",
            metadata=metadata,
        )

    def remove_clip_files(self, clip_paths: list[Path]) -> None:
        roots = {path.parent for path in clip_paths}
        for root in roots:
            safe_rmtree(root)

    def remove_generation_file(self, output_path: Path | None) -> None:
        safe_unlink(output_path)

    def probe_output_duration(self, output_path: Path) -> float | None:
        try:
            return self._probe_audio(output_path).duration_seconds
        except Exception:
            return None

    def ffmpeg_available(self) -> bool:
        return self._tool_available(self.settings.ffmpeg_bin)

    def ffprobe_available(self) -> bool:
        return self._tool_available(self.settings.ffprobe_bin)

    def _normalize_audio(self, source: Path, destination: Path) -> None:
        command = [
            self.settings.ffmpeg_bin,
            "-y",
            "-i",
            str(source),
            "-ac",
            "1",
            "-ar",
            "24000",
            "-sample_fmt",
            "s16",
            str(destination),
        ]
        subprocess.run(command, capture_output=True, check=True)

    def _probe_audio(self, source: Path) -> AudioMetadata:
        command = [
            self.settings.ffprobe_bin,
            "-v",
            "error",
            "-print_format",
            "json",
            "-show_streams",
            "-show_format",
            str(source),
        ]
        result = subprocess.run(command, capture_output=True, check=True, text=True)
        payload = json.loads(result.stdout)
        audio_stream = next((stream for stream in payload.get("streams", []) if stream.get("codec_type") == "audio"), None)
        if not audio_stream:
            raise AppError("No audio stream found in file.", 400, "invalid_audio")
        duration = float(payload.get("format", {}).get("duration") or 0.0)
        return AudioMetadata(
            duration_seconds=duration,
            sample_rate=int(audio_stream.get("sample_rate") or 0),
            channels=int(audio_stream.get("channels") or 0),
        )

    def _tool_available(self, tool_name: str) -> bool:
        return shutil.which(tool_name) is not None
