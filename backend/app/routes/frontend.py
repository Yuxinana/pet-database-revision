from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..core.config import FRONTEND_DIST, FRONTEND_INDEX


router = APIRouter(include_in_schema=False)


@router.get("/")
def frontend_root() -> FileResponse:
    built_index = FRONTEND_DIST / "index.html"
    return FileResponse(built_index if built_index.exists() else FRONTEND_INDEX)
