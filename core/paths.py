import sys
from pathlib import Path
from .config_manager import get_data_path

if getattr(sys, 'frozen', False):
    # PyInstaller one-dir mode: sys.executable is the .exe
    # _internal is in the same directory as the .exe
    APP_DIR = Path(sys.executable).parent / "_internal"
else:
    APP_DIR = Path(__file__).resolve().parent.parent

ASSETS_DIR = APP_DIR / "assets"

def get_db_path() -> Path:
    data_path = get_data_path()
    if data_path:
        return data_path / "res_stack_recorder.db"
    return APP_DIR / "res_stack_recorder.db"

def get_videos_dir() -> Path:
    data_path = get_data_path()
    if data_path:
        return data_path / "videos"
    return APP_DIR / "videos"

def get_snap_dir() -> Path:
    data_path = get_data_path()
    if data_path:
        return data_path / "snapshots"
    return APP_DIR / "snapshots"

# Ensure assets dir exists (others are ensured by main or usage)
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
