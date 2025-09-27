# main.py
# RES Stack Assembly Recorder – Material 3–inspired Dashboard
# Tech: Python 3.10+, PySide6 (Qt6), SQLite (built-in)
# Features:
# - Data entry: project info, operator, datetime, remarks, video upload
# - Auto-copy uploaded video into ./videos/
# - Record list with search, sort, quick filters
# - Video preview & playback (QtMultimedia) + Snapshot to ./snapshots/
# - Brand styling (Material 3 vibe) with RES colors
#
# Run:
#   pip install -r requirements.txt
#   python main.py
#
# Notes:
# - On Linux you may need GStreamer codecs for video playback.
# - Put your logo at ./assets/res_logo.png (optional).

import sys, os, sqlite3, shutil, datetime
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import (Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel,
                            QUrl)
from PySide6.QtGui import (QPixmap)
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFileDialog, QMessageBox,
    QHBoxLayout, QVBoxLayout, QFormLayout, QLineEdit, QTextEdit, QPushButton,
    QLabel, QDateTimeEdit, QSplitter, QTableView, QStyle, QToolButton, QFrame,
    QComboBox
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput, QVideoSink
from PySide6.QtMultimediaWidgets import QVideoWidget

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "res_stack_recorder.db"
VIDEOS_DIR = APP_DIR / "videos"
SNAP_DIR = APP_DIR / "snapshots"
ASSETS_DIR = APP_DIR / "assets"
for d in (VIDEOS_DIR, SNAP_DIR, ASSETS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ---------- COLORS (Material 3-ish, RES brand) ----------
COLORS = {
    "primary": "#22307B",      # RES navy
    "primaryContainer": "#E0E3FF",
    "onPrimary": "#FFFFFF",
    "secondary": "#4A5BD3",
    "surface": "#F6F7FB",
    "surfaceVariant": "#ECEEF7",
    "onSurface": "#0F172A",
    "outline": "#C7CCE5",
}

def material_stylesheet():
    c = COLORS
    return f"""
    * {{
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
        color: {c['onSurface']};
    }}
    QMainWindow, QWidget {{
        background: {c['surface']};
    }}
    QLineEdit, QTextEdit, QComboBox, QDateTimeEdit {{
        background: white;
        border: 1px solid {c['outline']};
        border-radius: 10px;
        padding: 8px 10px;
    }}
    QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QDateTimeEdit:focus {{
        border: 2px solid {c['secondary']};
    }}
    QPushButton.primary {{
        background: {c['primary']};
        color: {c['onPrimary']};
        border: none; border-radius: 12px; padding: 10px 14px;
        font-weight: 600;
    }}
    QPushButton.primary:hover {{ background: {c['secondary']}; }}
    QPushButton.tonal {{
        background: {c['primaryContainer']};
        color: {c['primary']};
        border: none; border-radius: 12px; padding: 10px 14px;
        font-weight: 600;
    }}
    QPushButton.outlined {{
        background: transparent;
        color: {c['primary']};
        border: 1.5px solid {c['primary']};
        border-radius: 12px; padding: 8px 12px;
        font-weight: 600;
    }}
    QTableView {{
        background: white;
        border: 1px solid {c['outline']};
        border-radius: 12px;
        gridline-color: {c['outline']};
        selection-background-color: {c['primaryContainer']};
        selection-color: {c['primary']};
    }}
    QHeaderView::section {{
        background: {c['surfaceVariant']};
        border: none; padding: 8px; font-weight: 700;
    }}
    QSplitter::handle {{ background: {c['surfaceVariant']}; }}
    #Card {{ background: white; border: 1px solid {c['outline']}; border-radius: 16px; }}
    """

# ---------- DB ----------
def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS recordings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_name TEXT,
                project_no TEXT,
                log_id TEXT,
                battery_no TEXT,
                operator_name TEXT,
                datetime TEXT,
                remarks TEXT,
                video_path TEXT,
                duration_ms INTEGER DEFAULT NULL,
                created_at TEXT
            )
        """)
        con.commit()

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

class RecordingTableModel(QAbstractTableModel):
    HEADERS = ["ID", "Project", "Project No.", "Log ID", "Battery No.",
               "Operator", "Date/Time", "Remarks", "Video", "Duration (s)"]

    def __init__(self):
        super().__init__()
        self.rows: list[Recording] = []
        self.refresh()

    def refresh(self, search: str = ""):
        self.beginResetModel()
        self.rows.clear()
        with sqlite3.connect(DB_PATH) as con:
            cur = con.cursor()
            if search:
                s = f"%{search.lower()}%"
                cur.execute("""
                    SELECT id, project_name, project_no, log_id, battery_no, operator_name,
                           datetime, remarks, video_path, duration_ms, created_at
                    FROM recordings
                    WHERE lower(project_name) LIKE ? OR lower(project_no) LIKE ?
                          OR lower(log_id) LIKE ? OR lower(battery_no) LIKE ?
                          OR lower(operator_name) LIKE ? OR lower(remarks) LIKE ?
                    ORDER BY datetime(created_at) DESC
                """, (s,s,s,s,s,s))
            else:
                cur.execute("""
                    SELECT id, project_name, project_no, log_id, battery_no, operator_name,
                           datetime, remarks, video_path, duration_ms, created_at
                    FROM recordings
                    ORDER BY datetime(created_at) DESC
                """)
            for rec in cur.fetchall():
                self.rows.append(Recording(*rec))
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()): return len(self.rows)
    def columnCount(self, parent=QModelIndex()): return len(self.HEADERS)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid(): return None
        r = self.rows[index.row()]
        c = index.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            mapping = [
                r.id, r.project_name, r.project_no, r.log_id, r.battery_no,
                r.operator_name, r.datetime, r.remarks,
                Path(r.video_path).name if r.video_path else "",
                f"{(r.duration_ms or 0)/1000:.1f}",
            ]
            return mapping[c]
        return None

    def headerData(self, sec, orient, role=Qt.DisplayRole):
        if orient == Qt.Horizontal and role == Qt.DisplayRole:
            return self.HEADERS[sec]
        return super().headerData(sec, orient, role)

    def recording_at(self, row: int) -> Recording | None:
        return self.rows[row] if 0 <= row < len(self.rows) else None

# ---------- UI ----------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RES – Stack Assembly Dashboard")
        self.setMinimumSize(1280, 800)
        self.setStyleSheet(material_stylesheet())
        self.currentVideoPath: Path | None = None

        header = self._build_header()
        splitter = QSplitter()
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(self._build_form_card())
        splitter.addWidget(self._build_list_and_player())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        root = QVBoxLayout()
        root.addWidget(header)
        root.addWidget(splitter)

        host = QWidget(); host.setLayout(root)
        self.setCentralWidget(host)
        self._connect_signals()

    # --- Header
    def _build_header(self) -> QWidget:
        bar = QFrame(); bar.setObjectName("Card")
        layout = QHBoxLayout(bar); layout.setContentsMargins(16, 10, 16, 10)

        logo = QLabel()
        logo_path = ASSETS_DIR / "res_logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("RES")
        title = QLabel("RES • Stack Assembly Dashboard")
        title.setStyleSheet(f"font-size:20px; font-weight:800; color:{COLORS['primary']};")

        layout.addWidget(logo); layout.addSpacing(8); layout.addWidget(title); layout.addStretch(1)

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Search projects, operators, remarks…")
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setFixedWidth(420)
        layout.addWidget(self.searchEdit)
        return bar

    # --- Left: Data entry card
    def _build_form_card(self) -> QWidget:
        card = QFrame(); card.setObjectName("Card")
        lay = QVBoxLayout(card); lay.setContentsMargins(16,16,16,16)

        h = QLabel("New Recording"); h.setStyleSheet("font-size:16px; font-weight:700;")
        lay.addWidget(h)

        form = QFormLayout(); form.setLabelAlignment(Qt.AlignLeft); form.setFormAlignment(Qt.AlignTop)
        self.projectName = QLineEdit()
        self.projectNo = QLineEdit()
        self.logId = QLineEdit()
        self.batteryNo = QLineEdit()
        self.operatorName = QLineEdit()
        self.dtEdit = QDateTimeEdit(datetime.datetime.now()); self.dtEdit.setCalendarPopup(True)
        self.dtEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.remarks = QTextEdit(); self.remarks.setFixedHeight(80)
        self.videoPathEdit = QLineEdit(); self.videoPathEdit.setReadOnly(True)
        self.browseBtn = QPushButton("Choose Video"); self.browseBtn.setProperty("class", "outlined")

        row = QHBoxLayout(); row.addWidget(self.videoPathEdit, 1); row.addWidget(self.browseBtn)

        form.addRow("Project name", self.projectName)
        form.addRow("Project No.", self.projectNo)
        form.addRow("Log ID", self.logId)
        form.addRow("Battery no.", self.batteryNo)
        form.addRow("Operator name", self.operatorName)
        form.addRow("Date & time", self.dtEdit)
        form.addRow("Remarks", self.remarks)
        # hack: add a container widget to host the row layout
        container = QWidget(); container.setLayout(row)
        form.addRow("Video upload", container)
        lay.addLayout(form)

        actions = QHBoxLayout()
        self.saveBtn = QPushButton("Save Entry"); self.saveBtn.setProperty("class", "primary")
        self.clearBtn = QPushButton("Clear"); self.clearBtn.setProperty("class", "tonal")
        actions.addWidget(self.saveBtn); actions.addWidget(self.clearBtn); actions.addStretch(1)
        lay.addLayout(actions)
        return card

    # --- Right: list + player
    def _build_list_and_player(self) -> QWidget:
        self.model = RecordingTableModel()
        self.proxy = QSortFilterProxyModel()
        self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.proxy.setFilterKeyColumn(-1)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setMinimumHeight(280)
        self.table.doubleClicked.connect(self._load_selected_video)

        # Quick filter row
        quick = QHBoxLayout()
        quick.addWidget(QLabel("Quick Filter:"))
        self.filterField = QComboBox()
        self.filterField.addItems(["All", "Project", "Project No.", "Log ID", "Battery no.", "Operator"])
        self.filterEdit = QLineEdit()
        self.filterEdit.setPlaceholderText("Type to filter…")
        self.filterEdit.setClearButtonEnabled(True)
        quick.addWidget(self.filterField); quick.addWidget(self.filterEdit, 1)

        # Player card
        playerCard = QFrame(); playerCard.setObjectName("Card")
        ply = QVBoxLayout(playerCard); ply.setContentsMargins(12,12,12,12)
        self.videoWidget = QVideoWidget(); self.videoWidget.setMinimumHeight(360)

        self.player = QMediaPlayer()
        self.audioOut = QAudioOutput(); self.player.setAudioOutput(self.audioOut)
        self.player.setVideoOutput(self.videoWidget)
        self.videoSink = QVideoSink(); self.player.setVideoSink(self.videoSink)

        controls = QHBoxLayout()
        self.playBtn = QPushButton(self.style().standardIcon(QStyle.SP_MediaPlay), "Play")
        self.pauseBtn = QPushButton(self.style().standardIcon(QStyle.SP_MediaPause), "Pause")
        self.stopBtn = QPushButton(self.style().standardIcon(QStyle.SP_MediaStop), "Stop")
        self.snapshotBtn = QPushButton("Snapshot"); self.snapshotBtn.setProperty("class", "outlined")
        controls.addWidget(self.playBtn); controls.addWidget(self.pauseBtn); controls.addWidget(self.stopBtn)
        controls.addStretch(1); controls.addWidget(self.snapshotBtn)

        ply.addWidget(self.videoWidget); ply.addLayout(controls)

        right = QWidget(); v = QVBoxLayout(right); v.setContentsMargins(0,0,0,0)
        v.addLayout(quick); v.addWidget(self.table, 1); v.addWidget(playerCard, 2)
        return right

    # --- wire events
    def _connect_signals(self):
        self.browseBtn.clicked.connect(self._choose_video)
        self.saveBtn.clicked.connect(self._save_entry)
        self.clearBtn.clicked.connect(lambda: self._clear_form(keep_datetime=True))
        self.searchEdit.textChanged.connect(lambda t: self.model.refresh(t))
        self.filterEdit.textChanged.connect(self._apply_field_filter)
        self.playBtn.clicked.connect(self.player.play)
        self.pauseBtn.clicked.connect(self.player.pause)
        self.stopBtn.clicked.connect(self.player.stop)
        self.snapshotBtn.clicked.connect(self._snapshot)

    # --- handlers
    def _choose_video(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Video", str(Path.home()),
            "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )
        if path: self.videoPathEdit.setText(path)

    def _save_entry(self):
        if not self.projectName.text().strip():
            QMessageBox.warning(self, "Missing", "Project name is required."); return
        if not self.videoPathEdit.text().strip():
            QMessageBox.warning(self, "Missing", "Please choose a video file."); return

        src = Path(self.videoPathEdit.text().strip())
        if not src.exists():
            QMessageBox.critical(self, "Error", "Selected video file not found."); return

        # copy into ./videos with a unique name
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = VIDEOS_DIR / f"{ts}_{src.name}"
        try:
            shutil.copy2(src, dst)
        except Exception as e:
            QMessageBox.critical(self, "Copy failed", f"Could not copy video:\n{e}"); return

        values = (
            self.projectName.text().strip(),
            self.projectNo.text().strip(),
            self.logId.text().strip(),
            self.batteryNo.text().strip(),
            self.operatorName.text().strip(),
            self.dtEdit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            self.remarks.toPlainText().strip(),
            str(dst), None, datetime.datetime.now().isoformat(timespec='seconds')
        )
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""
                INSERT INTO recordings (project_name, project_no, log_id, battery_no, operator_name,
                                        datetime, remarks, video_path, duration_ms, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, values)
            con.commit()

        self.model.refresh()
        self._clear_form(keep_datetime=True)
        QMessageBox.information(self, "Saved", "Recording saved successfully.")

    def _clear_form(self, keep_datetime=False):
        self.projectName.clear(); self.projectNo.clear(); self.logId.clear()
        self.batteryNo.clear(); self.operatorName.clear()
        if not keep_datetime:
            self.dtEdit.setDateTime(datetime.datetime.now())
        self.remarks.clear(); self.videoPathEdit.clear()

    def _apply_field_filter(self, text: str):
        map_col = {
            "All": -1, "Project": 1, "Project No.": 2, "Log ID": 3,
            "Battery no.": 4, "Operator": 5
        }
        col = map_col.get(self.filterField.currentText(), -1)
        self.proxy.setFilterKeyColumn(col if col >= 0 else -1)
        self.proxy.setFilterFixedString(text)

    def _load_selected_video(self):
        idx = self.table.currentIndex()
        if not idx.isValid(): return
        src_idx = self.proxy.mapToSource(idx)
        rec = self.model.recording_at(src_idx.row())
        if not rec: return
        if rec.video_path and Path(rec.video_path).exists():
            self.player.setSource(QUrl.fromLocalFile(rec.video_path))
            self.player.play()
            self.currentVideoPath = Path(rec.video_path)
        else:
            QMessageBox.warning(self, "Missing file", "Video file not found on disk.")

    def _snapshot(self):
        # take a frame via QVideoSink
        frame = self.player.videoSink().videoFrame() if self.player.videoSink() else None
        if not frame or not frame.isValid():
            QMessageBox.warning(self, "No frame", "Play the video, then try Snapshot again."); return
        image = frame.toImage()
        if image.isNull():
            QMessageBox.critical(self, "Error", "Could not read current frame."); return
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = self.currentVideoPath.stem if self.currentVideoPath else "snapshot"
        out = SNAP_DIR / f"{stem}_{ts}.png"
        if image.save(str(out)):
            QMessageBox.information(self, "Saved", f"Snapshot saved to:\n{out}")
        else:
            QMessageBox.critical(self, "Error", "Failed to save snapshot.")

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("RES – Stack Assembly Dashboard")
    win = MainWindow(); win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
