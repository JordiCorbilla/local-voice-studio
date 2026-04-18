from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_container, get_db_session
from app.api.mappers import map_clip, map_profile_detail, map_profile_summary
from app.core.container import AppContainer
from app.core.errors import AppError
from app.schemas.profile import (
    ClipTranscriptUpdate,
    ProfileCreate,
    ProfileDetail,
    ProfileSummary,
    ProfileUpdate,
    ReferenceClip,
)

router = APIRouter(prefix="/profiles", tags=["profiles"])


def _translate_error(exc: AppError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("", response_model=list[ProfileSummary])
def list_profiles(
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    return [map_profile_summary(profile) for profile in container.profile_service.list_profiles(session)]


@router.post("", response_model=ProfileDetail, status_code=status.HTTP_201_CREATED)
def create_profile(
    payload: ProfileCreate,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        profile = container.profile_service.create_profile(session, payload)
        return map_profile_detail(profile)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.get("/{profile_id}", response_model=ProfileDetail)
def get_profile(
    profile_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        profile = container.profile_service.get_profile(session, profile_id)
        return map_profile_detail(profile)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.patch("/{profile_id}", response_model=ProfileDetail)
def update_profile(
    profile_id: str,
    payload: ProfileUpdate,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        profile = container.profile_service.update_profile(session, profile_id, payload)
        return map_profile_detail(profile)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.delete("/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        container.profile_service.delete_profile(session, profile_id)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.get("/{profile_id}/clips", response_model=list[ReferenceClip])
def list_clips(
    profile_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        clips = container.profile_service.list_clips(session, profile_id)
        return [map_clip(clip) for clip in clips]
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.post("/{profile_id}/clips/upload", response_model=ReferenceClip, status_code=status.HTTP_201_CREATED)
async def upload_clip(
    profile_id: str,
    file: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        clip = container.profile_service.add_clip(
            session,
            profile_id=profile_id,
            filename=file.filename or "reference.wav",
            content_type=file.content_type or "application/octet-stream",
            payload=await file.read(),
        )
        return map_clip(clip)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.post("/{profile_id}/clips/recording", response_model=ReferenceClip, status_code=status.HTTP_201_CREATED)
async def upload_recording(
    profile_id: str,
    recording: UploadFile = File(...),
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        clip = container.profile_service.add_clip(
            session,
            profile_id=profile_id,
            filename=recording.filename or "recording.webm",
            content_type=recording.content_type or "audio/webm",
            payload=await recording.read(),
        )
        return map_clip(clip)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.delete("/{profile_id}/clips/{clip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_clip(
    profile_id: str,
    clip_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        container.profile_service.delete_clip(session, profile_id, clip_id)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.post("/{profile_id}/clips/{clip_id}/set-primary", response_model=ProfileDetail)
def set_primary_clip(
    profile_id: str,
    clip_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        profile = container.profile_service.set_primary_clip(session, profile_id, clip_id)
        return map_profile_detail(profile)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.patch("/{profile_id}/clips/{clip_id}", response_model=ReferenceClip)
def update_clip_transcript(
    profile_id: str,
    clip_id: str,
    payload: ClipTranscriptUpdate,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        clip = container.profile_service.update_clip_reference_text(
            session,
            profile_id=profile_id,
            clip_id=clip_id,
            reference_text=payload.reference_text,
        )
        return map_clip(clip)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.post("/{profile_id}/clips/{clip_id}/transcribe", response_model=ReferenceClip)
def transcribe_clip(
    profile_id: str,
    clip_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        clip = container.profile_service.get_clip(session, profile_id, clip_id)
        transcript = container.transcription_service.transcribe(
            Path(clip.normalized_path),
            language=container.profile_service.get_profile(session, profile_id).language_preference,
        )
        clip = container.profile_service.update_clip_reference_text(
            session,
            profile_id=profile_id,
            clip_id=clip_id,
            reference_text=transcript,
            transcript_source="transcribed",
        )
        return map_clip(clip)
    except AppError as exc:
        raise _translate_error(exc) from exc
