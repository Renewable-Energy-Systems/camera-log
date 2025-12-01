# views/dashboard.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QSizePolicy, QSpacerItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout
)
from PySide6.QtCore import Qt
from core.db import query

CARD_W = 360
CARD_H = 220

def _kpi_card(title: str, value: str, icon_name: str = None) -> QFrame:
    card = QFrame(); card.setObjectName("Card")
    card.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
    v = QVBoxLayout(card); v.setContentsMargins(24, 24, 24, 24); v.setSpacing(8)
    t = QLabel(title); t.setStyleSheet("font-size: 14px; font-weight: 600; color: #46464F;")
    val = QLabel(value); val.setStyleSheet("font-size: 32px; font-weight: 800; color: #1B1B1F;")
    v.addWidget(t); v.addWidget(val); v.addStretch(1)
    return card

class DashboardView(QWidget):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self); root.setContentsMargins(12,8,12,12); root.setSpacing(24)

        # Header
        header = QLabel("Dashboard Overview")
        header.setStyleSheet("font-size: 24px; font-weight: 700; color: #1B1B1F;")
        root.addWidget(header)

        # KPI Grid
        self.grid = QGridLayout(); self.grid.setSpacing(24)
        root.addLayout(self.grid)
        
        # Recent Activity Table
        lblRecent = QLabel("Recent Activity")
        lblRecent.setStyleSheet("font-size: 18px; font-weight: 600; color: #1B1B1F; margin-top: 12px;")
        root.addWidget(lblRecent)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Battery Name", "Battery Code", "Battery No.", "Operator", "Date/Time", "Remarks"])
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch) # Remarks stretch
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.NoSelection)
        self.table.setFocusPolicy(Qt.NoFocus)
        self.table.setAlternatingRowColors(True)
        # Height for ~10 rows + header
        self.table.setMinimumHeight(350)
        
        root.addWidget(self.table)
        
        self.refresh()

    def refresh(self):
        # 1. Stats
        total = query("SELECT COUNT(*) FROM recordings")[0][0]
        latest = query("SELECT IFNULL(MAX(datetime), '-') FROM recordings")[0][0]
        with_video = query("SELECT COUNT(*) FROM recordings WHERE video_path IS NOT NULL AND length(video_path)>0")[0][0]

        # Clear grid
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        self.grid.addWidget(_kpi_card("Total Recordings", str(total)), 0, 0)
        self.grid.addWidget(_kpi_card("Last Recording", str(latest)), 0, 1)
        self.grid.addWidget(_kpi_card("Entries with Video", str(with_video)), 0, 2)

        # 2. Table
        rows = query("""
            SELECT battery_name, battery_code, battery_no, operator_name, datetime, remarks
            FROM recordings
            ORDER BY datetime(created_at) DESC
            LIMIT 10
        """)
        
        self.table.setRowCount(0)
        for r_idx, row_data in enumerate(rows):
            self.table.insertRow(r_idx)
            for c_idx, val in enumerate(row_data):
                item = QTableWidgetItem(str(val) if val else "")
                item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                self.table.setItem(r_idx, c_idx, item)
