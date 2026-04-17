from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_container, get_db_session
from app.api.mappers import map_generation
from app.core.container import AppContainer
from app.core.errors import AppError
from app.schemas.generation import GenerationRecord, GenerationRequest

router = APIRouter(prefix="/generations", tags=["generations"])


def _translate_error(exc: AppError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail={"code": exc.code, "message": exc.message})


@router.get("", response_model=list[GenerationRecord])
def list_generations(
    profile_id: str | None = Query(default=None),
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    return [map_generation(record) for record in container.generation_service.list_generations(session, profile_id)]


@router.post("", response_model=GenerationRecord, status_code=status.HTTP_202_ACCEPTED)
def create_generation(
    payload: GenerationRequest,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        record = container.generation_service.enqueue_generation(session, payload)
        return map_generation(record)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.get("/{generation_id}", response_model=GenerationRecord)
def get_generation(
    generation_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        record = container.generation_service.get_generation(session, generation_id)
        return map_generation(record)
    except AppError as exc:
        raise _translate_error(exc) from exc


@router.delete("/{generation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_generation(
    generation_id: str,
    session: Session = Depends(get_db_session),
    container: AppContainer = Depends(get_container),
):
    try:
        container.generation_service.delete_generation(session, generation_id)
    except AppError as exc:
        raise _translate_error(exc) from exc
