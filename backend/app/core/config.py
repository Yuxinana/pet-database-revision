from __future__ import annotations

from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[3]
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"
LEGACY_UI_PATH = ROOT_DIR / "frontend" / "legacy" / "pawtrack_demo.html"
