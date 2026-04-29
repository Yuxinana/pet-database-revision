from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .core.config import FRONTEND_DIST
from .core.errors import register_exception_handlers
from .core.legacy import initialize_database
from .routes import api, frontend


@asynccontextmanager
async def lifespan(_app: FastAPI):
    reset = os.environ.get("PAWTRACK_RESET_DB", "").lower() in {"1", "true", "yes"}
    initialize_database(reset=reset)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="PawTrack API",
        version="2.0.0",
        description="FastAPI backend for the PawTrack pet adoption database.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "*").split(","),
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)
    app.include_router(frontend.router)
    app.include_router(api.router)

    if FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")

    return app


app = create_app()
