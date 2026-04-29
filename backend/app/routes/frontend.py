from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..core.config import LEGACY_UI_PATH


router = APIRouter(include_in_schema=False)


@router.get("/")
def frontend_root() -> FileResponse:
    return FileResponse(LEGACY_UI_PATH)


@router.get("/pawtrack_demo.html")
def legacy_frontend() -> FileResponse:
    return FileResponse(LEGACY_UI_PATH)


@router.get("/legacy")
def legacy_frontend_alias() -> FileResponse:
    return FileResponse(LEGACY_UI_PATH)
