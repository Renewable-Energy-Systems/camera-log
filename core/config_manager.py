import json
import os
from pathlib import Path
from typing import Optional

APP_NAME = "RES Stack Assembly Recorder"
CONFIG_DIR = Path(os.getenv('APPDATA')) / APP_NAME
CONFIG_FILE = CONFIG_DIR / "config.json"

def _ensure_config_dir():
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def load_config() -> dict:
    if not CONFIG_FILE.exists():
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}

def save_config(config: dict):
    _ensure_config_dir()
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

def get_data_path() -> Optional[Path]:
    config = load_config()
    path_str = config.get("data_path")
    if path_str:
        return Path(path_str)
    return None

def set_data_path(path: str | Path):
    config = load_config()
    config["data_path"] = str(path)
    save_config(config)

def get_app_data_dir() -> Path:
    return CONFIG_DIR
