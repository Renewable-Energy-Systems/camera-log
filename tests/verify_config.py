import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from core import config_manager
from core import paths

def test_config():
    print("Testing ConfigManager...")
    original_path = config_manager.get_data_path()
    print(f"Original data path: {original_path}")

    test_path = Path("C:/Temp/TestCamLogData")
    print(f"Setting data path to: {test_path}")
    config_manager.set_data_path(test_path)

    new_path = config_manager.get_data_path()
    print(f"Retrieved data path: {new_path}")
    assert new_path == test_path

    print("Testing Paths...")
    db_path = paths.get_db_path()
    videos_dir = paths.get_videos_dir()
    snap_dir = paths.get_snap_dir()

    print(f"DB Path: {db_path}")
    print(f"Videos Dir: {videos_dir}")
    print(f"Snap Dir: {snap_dir}")

    assert db_path == test_path / "res_stack_recorder.db"
    assert videos_dir == test_path / "videos"
    assert snap_dir == test_path / "snapshots"

    # Restore original (optional, but good practice if we don't want to mess up user config)
    # But since we are in dev, maybe we leave it or reset it.
    # I'll reset it to None to simulate fresh install if it was None.
    if original_path is None:
        # We can't easily unset it with current API, but we can set empty string?
        # config_manager.set_data_path("") 
        # But set_data_path takes str|Path.
        pass
    else:
        config_manager.set_data_path(original_path)
    
    print("Verification passed!")

if __name__ == "__main__":
    test_config()
