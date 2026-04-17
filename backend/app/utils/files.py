from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path


def safe_unlink(path: Path | None) -> None:
    if path and path.exists():
        path.unlink()


def safe_rmtree(path: Path | None) -> None:
    if path and path.exists():
        shutil.rmtree(path, ignore_errors=True)


def compute_profile_fingerprint(paths: list[Path]) -> str:
    payload: list[dict[str, object]] = []
    for path in sorted(paths):
        stat = path.stat()
        payload.append(
            {
                "path": str(path),
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def ensure_within(root: Path, candidate: Path) -> Path:
    root = root.resolve()
    candidate = candidate.resolve()
    if os.path.commonpath([str(root), str(candidate)]) != str(root):
        raise ValueError("Path escapes configured directory")
    return candidate
