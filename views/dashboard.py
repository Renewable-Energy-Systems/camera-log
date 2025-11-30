# views/dashboard.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSpacerItem
from core.db import query

CARD_W = 360
CARD_H = 220

def _kpi_card(title: str, value: str, icon_name: str = None) -> QFrame:
    card = QFrame(); card.setObjectName("Card")
    # card.setMinimumWidth(200) # Let layout handle width
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    
    v = QVBoxLayout(card); v.setContentsMargins(24, 24, 24, 24); v.setSpacing(8)
    
    t = QLabel(title); t.setStyleSheet("font-size: 14px; font-weight: 600; color: #46464F;")
    val = QLabel(value); val.setStyleSheet("font-size: 32px; font-weight: 800; color: #1B1B1F;")
    
    v.addWidget(t)
    v.addWidget(val)
    v.addStretch(1)
    
    return card

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(12,8,12,12); root.setSpacing(12)

        total = query("SELECT COUNT(*) FROM recordings")[0][0]
        latest = query("SELECT IFNULL(MAX(datetime), '-') FROM recordings")[0][0]
        with_video = query("SELECT COUNT(*) FROM recordings WHERE video_path IS NOT NULL AND length(video_path)>0")[0][0]

        # Header
        header = QLabel("Dashboard Overview")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: #1B1B1F; margin-bottom: 16px;")
        root.addWidget(header)

        # Grid for cards
        from PySide6.QtWidgets import QGridLayout
        grid = QGridLayout(); grid.setSpacing(24)
        
        # Cards
        c1 = _kpi_card("Total Recordings", str(total))
        c2 = _kpi_card("Last Recording", str(latest))
        c3 = _kpi_card("Entries with Video", str(with_video))
        
        grid.addWidget(c1, 0, 0)
        grid.addWidget(c2, 0, 1)
        grid.addWidget(c3, 0, 2)
        
        root.addLayout(grid)
        root.addStretch(1)
