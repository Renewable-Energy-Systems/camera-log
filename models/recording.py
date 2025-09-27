# models/recording.py
from dataclasses import dataclass

@dataclass
class Recording:
    id: int
    project_name: str
    project_no: str
    log_id: str
    battery_no: str
    operator_name: str
    datetime: str
    remarks: str
    video_path: str
    duration_ms: int | None
    created_at: str
