from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes_files import router as files_router
from app.api.routes_generation import router as generations_router
from app.api.routes_profiles import router as profiles_router
from app.api.routes_runtime import router as runtime_router
from app.core.container import AppContainer
from app.core.logging import configure_logging


def create_app(container: AppContainer | None = None) -> FastAPI:
    configure_logging()
    active_container = container or AppContainer()
    settings = active_container.settings

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        active_container.startup()
        app.state.container = active_container
        yield
        active_container.shutdown()

    app = FastAPI(title=settings.app_name, lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.cors_origin, "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(profiles_router, prefix=settings.api_prefix)
    app.include_router(generations_router, prefix=settings.api_prefix)
    app.include_router(files_router, prefix=settings.api_prefix)
    app.include_router(runtime_router, prefix=settings.api_prefix)
    return app


app = create_app()
