from __future__ import annotations

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.core.container import AppContainer
from app.schemas.runtime import HealthStatus, RuntimeInfo

router = APIRouter(tags=["runtime"])


@router.get("/health", response_model=HealthStatus)
def health(container: AppContainer = Depends(get_container)):
    return container.runtime_service.health(container.audio_service.ffmpeg_available())


@router.get("/runtime", response_model=RuntimeInfo)
def runtime(container: AppContainer = Depends(get_container)):
    return container.runtime_service.runtime_info(
        ffmpeg_available=container.audio_service.ffmpeg_available(),
        ffprobe_available=container.audio_service.ffprobe_available(),
    )
