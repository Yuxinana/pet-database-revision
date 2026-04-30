from __future__ import annotations

import sqlite3
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .service import ApiError


def error_payload(message: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"error": message, **(extra or {})}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(_request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(error_payload(exc.message, exc.payload), status_code=int(exc.status))

    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_error_handler(_request: Request, exc: sqlite3.IntegrityError) -> JSONResponse:
        return JSONResponse(
            error_payload(f"Database constraint failed: {exc}"),
            status_code=HTTPStatus.CONFLICT,
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(_request: Request, exc: ValueError) -> JSONResponse:
        return JSONResponse(error_payload(str(exc) or "Invalid request."), status_code=HTTPStatus.BAD_REQUEST)
