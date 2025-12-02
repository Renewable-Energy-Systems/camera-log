# services/media.py
import shutil, datetime
from pathlib import Path
import core.paths as paths
from core.settings import get_snapshot_dir

def copy_video_into_library(src: Path) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = paths.get_videos_dir() / f"{ts}_{src.name}"
    shutil.copy2(src, dst)
    return dst

def _snapshot_base_dir() -> Path:
    # operator-chosen dir (QSettings) or fallback to app snapshots
    return get_snapshot_dir() or paths.get_snap_dir()

def snapshot_filename(base_stem: str) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    base = _snapshot_base_dir()
    base.mkdir(parents=True, exist_ok=True)
    return base / f"{base_stem}_{ts}.png"
