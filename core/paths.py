# core/paths.py
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
DB_PATH = APP_DIR / "res_stack_recorder.db"
VIDEOS_DIR = APP_DIR / "videos"
SNAP_DIR = APP_DIR / "snapshots"
ASSETS_DIR = APP_DIR / "assets"

for p in (VIDEOS_DIR, SNAP_DIR, ASSETS_DIR):
    p.mkdir(parents=True, exist_ok=True)
