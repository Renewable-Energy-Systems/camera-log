# views/dashboard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSpacerItem
from core.db import query

CARD_W = 360
CARD_H = 220

def _kpi_card(title: str, value: str) -> QFrame:
    card = QFrame(); card.setObjectName("Card")
    card.setFixedSize(CARD_W, CARD_H)
    v = QVBoxLayout(card); v.setContentsMargins(16,16,16,16); v.setSpacing(8)
    t = QLabel(title); t.setStyleSheet("font-size:12px; color:#475569;")
    val = QLabel(value); val.setStyleSheet("font-size:28px; font-weight:900;")
    v.addWidget(t); v.addStretch(1); v.addWidget(val)
    return card

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(12,8,12,12); root.setSpacing(12)

        total = query("SELECT COUNT(*) FROM recordings")[0][0]
        latest = query("SELECT IFNULL(MAX(datetime), '-') FROM recordings")[0][0]
        with_video = query("SELECT COUNT(*) FROM recordings WHERE video_path IS NOT NULL AND length(video_path)>0")[0][0]

        row = QHBoxLayout(); row.setSpacing(16)
        row.addSpacerItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))
        row.addWidget(_kpi_card("Total recordings", str(total)))
        row.addWidget(_kpi_card("Last recording time", str(latest)))
        row.addWidget(_kpi_card("Entries with video", str(with_video)))
        row.addSpacerItem(QSpacerItem(0,0, QSizePolicy.Expanding, QSizePolicy.Minimum))

        root.addLayout(row)
