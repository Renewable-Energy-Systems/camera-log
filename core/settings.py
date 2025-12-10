# core/settings.py
from pathlib import Path
from PySide6.QtCore import QSettings

ORG = "RES"
APP = "StackAssemblyDashboard"
VERSION = "1.0.5"

def _s():
    st = QSettings(ORG, APP)
    st.sync()
    return st

def get_snapshot_dir() -> Path | None:
    v = _s().value("snapshot_dir", "")
    p = Path(v) if v else None
    return p if p and p.exists() else None

def set_snapshot_dir(p: Path):
    st = _s()
    st.setValue("snapshot_dir", str(p))
    st.sync()
