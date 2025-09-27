# services/media.py
import shutil, datetime
from pathlib import Path
from core.paths import VIDEOS_DIR, SNAP_DIR
from core.settings import get_snapshot_dir

def copy_video_into_library(src: Path) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = VIDEOS_DIR / f"{ts}_{src.name}"
    shutil.copy2(src, dst)
    return dst

def _snapshot_base_dir() -> Path:
    # operator-chosen dir (QSettings) or fallback to app snapshots
    return get_snapshot_dir() or SNAP_DIR

def snapshot_filename(base_stem: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = _snapshot_base_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{base_stem}_{ts}.png"
