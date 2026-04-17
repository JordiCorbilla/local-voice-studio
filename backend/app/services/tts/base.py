from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


@dataclass(slots=True)
class PreparedProfile:
    profile_id: str
    language: str
    reference_paths: list[Path]
    primary_reference_path: Path
    conditioning_artifact_path: Path | None
    conditioning_fingerprint: str


@dataclass(slots=True)
class SynthesisPayload:
    text: str
    language: str
    parameters: dict[str, Any]


class TtsEngine(Protocol):
    def load_model(self) -> None: ...
    def is_ready(self) -> bool: ...
    def prepare_profile(self, profile: PreparedProfile) -> PreparedProfile: ...
    def synthesize(self, profile: PreparedProfile, payload: SynthesisPayload, output_path: Path) -> None: ...
    def get_runtime_info(self) -> dict[str, Any]: ...
