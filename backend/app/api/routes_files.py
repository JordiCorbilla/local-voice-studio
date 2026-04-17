from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.api.dependencies import get_container
from app.core.container import AppContainer
from app.utils.files import ensure_within

router = APIRouter(prefix="/files", tags=["files"])


@router.get("/generated/{filename}")
def serve_generated_file(filename: str, container: AppContainer = Depends(get_container)):
    try:
        target = ensure_within(container.settings.generated_dir, container.settings.generated_dir / filename)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_path", "message": str(exc)}) from exc
    if not target.exists():
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Generated file not found."})
    return FileResponse(target)


@router.get("/reference/{relative_path:path}")
def serve_reference_file(relative_path: str, container: AppContainer = Depends(get_container)):
    try:
        target = ensure_within(container.settings.profiles_dir, container.settings.profiles_dir / Path(relative_path))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"code": "invalid_path", "message": str(exc)}) from exc
    if not target.exists():
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Reference file not found."})
    return FileResponse(target)
