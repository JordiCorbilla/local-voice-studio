from __future__ import annotations

from collections.abc import Generator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.container import AppContainer


def get_container(request: Request) -> AppContainer:
    return request.app.state.container


def get_db_session(container: AppContainer = Depends(get_container)) -> Generator[Session, None, None]:
    with container.session_factory() as session:
        yield session
