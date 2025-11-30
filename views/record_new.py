# views/record_new.py
import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QTextEdit,
                               QPushButton, QHBoxLayout, QFileDialog, QDateTimeEdit, QMessageBox, 
                               QFrame, QProgressDialog, QGridLayout, QScrollArea, QSizePolicy, QStyle)
from PySide6.QtGui import QPixmap, QIcon
from core.db import execute
from core.paths import VIDEOS_DIR, ASSETS_DIR
from services.media import copy_video_into_library
from services.video_processor import process_and_save_video

class VideoSaveWorker(QThread):
    finished = Signal(bool, str)

    def __init__(self, src, dst, data):
        super().__init__()
        self.src = src
        self.dst = dst
        self.data = data

    def run(self):
        try:
            process_and_save_video(self.src, self.dst, self.data)
            self.finished.emit(True, self.dst)
        except Exception as e:
            self.finished.emit(False, str(e))

class RecordNewView(QFrame):
    def __init__(self, on_saved=None):
        super().__init__()
        self.setObjectName("RecordNewView")
        self.on_saved = on_saved
        
        # Main Layout
        main_layout = QVBoxLayout(self); main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Scroll Area
        scroll = QScrollArea(); scroll.setWidgetResizable(True); scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        # Content Widget
        content = QWidget()
        content.setMaximumWidth(900)
        self.layout = QVBoxLayout(content); self.layout.setSpacing(24); self.layout.setContentsMargins(24, 24, 24, 24)
        
        # 1. Header Section
        self._setup_header()
        
        # 2. Project Details Card
        self._setup_project_card()
        
        # 3. Session Details Card
        self._setup_session_card()
        
        # 4. Media Card
        self._setup_media_card()
        
        # 5. Remarks Card
        self._setup_remarks_card()
        
        # 6. Actions
        self._setup_actions()
        
        # Wrapper for centering
        wrapper = QWidget()
        wl = QHBoxLayout(wrapper); wl.setContentsMargins(0,0,0,0)
        wl.addStretch(1); wl.addWidget(content); wl.addStretch(1)
        
        scroll.setWidget(wrapper)
        main_layout.addWidget(scroll)

    def _setup_header(self):
        # Image
        header_img = QLabel()
        pix = QPixmap(str(ASSETS_DIR / "recording_header.png"))
        if not pix.isNull():
            header_img.setPixmap(pix.scaledToWidth(900, Qt.SmoothTransformation))
            header_img.setFixedHeight(200)
            header_img.setScaledContents(True)
            header_img.setStyleSheet("border-radius: 12px;")
            self.layout.addWidget(header_img)
        
        # Title
        title = QLabel("New Recording Entry")
        title.setStyleSheet("font-size: 28px; font-weight: 800; color: #1B1B1F; margin-top: 8px;")
        self.layout.addWidget(title)
        
        subtitle = QLabel("Fill in the details below to log a new stack assembly recording.")
        subtitle.setStyleSheet("font-size: 14px; color: #5B5D72; margin-bottom: 8px;")
        self.layout.addWidget(subtitle)

    def _create_card(self, title):
        card = QFrame(); card.setObjectName("Card")
        l = QVBoxLayout(card); l.setContentsMargins(20, 20, 20, 20); l.setSpacing(16)
        
        lbl = QLabel(title)
        lbl.setStyleSheet("font-size: 18px; font-weight: 700; color: #3448A3; margin-bottom: 8px;")
        l.addWidget(lbl)
        return card, l

    def _setup_project_card(self):
        card, l = self._create_card("Project Information")
        grid = QGridLayout(); grid.setSpacing(16)
        
        self.projectName = QLineEdit(); self.projectName.setPlaceholderText("e.g. Solar Farm A")
        self.projectNo = QLineEdit(); self.projectNo.setPlaceholderText("e.g. P-2025-001")
        self.logId = QLineEdit(); self.logId.setPlaceholderText("e.g. L-105")
        
        self._add_field(grid, 0, 0, "Project Name", self.projectName)
        self._add_field(grid, 0, 1, "Project No.", self.projectNo)
        self._add_field(grid, 1, 0, "Log ID", self.logId)
        
        l.addLayout(grid)
        self.layout.addWidget(card)

    def _setup_session_card(self):
        card, l = self._create_card("Session Details")
        grid = QGridLayout(); grid.setSpacing(16)
        
        self.batteryNo = QLineEdit(); self.batteryNo.setPlaceholderText("e.g. B-12")
        self.operatorName = QLineEdit(); self.operatorName.setPlaceholderText("e.g. John Doe")
        self.dtEdit = QDateTimeEdit(datetime.datetime.now()); self.dtEdit.setCalendarPopup(True)
        self.dtEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        
        self._add_field(grid, 0, 0, "Battery No.", self.batteryNo)
        self._add_field(grid, 0, 1, "Operator Name", self.operatorName)
        self._add_field(grid, 1, 0, "Date & Time", self.dtEdit)
        
        l.addLayout(grid)
        self.layout.addWidget(card)

    def _setup_media_card(self):
        card, l = self._create_card("Video Source")
        
        row = QHBoxLayout(); row.setSpacing(12)
        
        self.videoPathEdit = QLineEdit(); self.videoPathEdit.setReadOnly(True)
        self.videoPathEdit.setPlaceholderText("No video selected...")
        
        self.browseBtn = QPushButton("Select Video File")
        self.browseBtn.setProperty("class", "tonal")
        self.browseBtn.setCursor(Qt.PointingHandCursor)
        self.browseBtn.setIcon(self.style().standardIcon(QStyle.SP_DirIcon))
        self.browseBtn.clicked.connect(self._choose_video)
        
        row.addWidget(self.videoPathEdit, 1)
        row.addWidget(self.browseBtn)
        
        l.addLayout(row)
        
        hint = QLabel("Supported formats: MP4, MOV, AVI, MKV")
        hint.setStyleSheet("color: #767680; font-size: 12px; font-style: italic;")
        l.addWidget(hint)
        
        self.layout.addWidget(card)

    def _setup_remarks_card(self):
        card, l = self._create_card("Additional Notes")
        
        self.remarks = QTextEdit()
        self.remarks.setPlaceholderText("Enter any observations or issues encountered during assembly...")
        self.remarks.setFixedHeight(100)
        
        l.addWidget(self.remarks)
        self.layout.addWidget(card)

    def _setup_actions(self):
        row = QHBoxLayout(); row.setSpacing(16)
        row.addStretch(1)
        
        self.clearBtn = QPushButton("Clear Form")
        self.clearBtn.setProperty("class", "text")
        self.clearBtn.setCursor(Qt.PointingHandCursor)
        self.clearBtn.clicked.connect(self._clear)
        
        self.saveBtn = QPushButton("Save Recording")
        self.saveBtn.setProperty("class", "primary")
        self.saveBtn.setCursor(Qt.PointingHandCursor)
        self.saveBtn.setMinimumWidth(150)
        self.saveBtn.clicked.connect(self._save)
        
        row.addWidget(self.clearBtn)
        row.addWidget(self.saveBtn)
        
        self.layout.addLayout(row)
        self.layout.addStretch(1)

    def _add_field(self, grid, row, col, label, widget):
        l = QLabel(label)
        l.setStyleSheet("font-weight: 600; color: #46464F; margin-bottom: 4px;")
        
        v = QVBoxLayout(); v.setSpacing(0); v.setContentsMargins(0,0,0,0)
        v.addWidget(l)
        v.addWidget(widget)
        
        grid.addLayout(v, row, col)

    def _choose_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", str(Path.home()),
                                              "Video Files (*.mp4 *.mov *.avi *.mkv)")
        if path: self.videoPathEdit.setText(path)

    def _clear(self):
        self.projectName.clear(); self.projectNo.clear(); self.logId.clear()
        self.batteryNo.clear(); self.operatorName.clear(); self.remarks.clear()
        self.videoPathEdit.clear()
        self.dtEdit.setDateTime(datetime.datetime.now())

    def _save(self):
        if not self.projectName.text().strip():
            QMessageBox.warning(self, "Missing", "Project name is required."); return
        if not self.videoPathEdit.text().strip():
            QMessageBox.warning(self, "Missing", "Please choose a video file."); return

        src = Path(self.videoPathEdit.text().strip())
        if not src.exists():
            QMessageBox.critical(self, "Error", "Selected video file not found."); return

        # Define destination
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = VIDEOS_DIR / f"{ts}_{src.name}"
        
        # Prepare data for overlay
        data = (
            self.projectNo.text().strip(),
            self.batteryNo.text().strip(),
            self.operatorName.text().strip()
        )

        # Progress Dialog
        self.pd = QProgressDialog("Processing and saving video...", None, 0, 0, self)
        self.pd.setWindowModality(Qt.WindowModal)
        self.pd.setMinimumDuration(0)
        self.pd.show()

        # Worker
        self.worker = VideoSaveWorker(str(src), str(dst), data)
        self.worker.finished.connect(lambda s, m: self._on_save_finished(s, m, dst))
        self.worker.start()

    def _on_save_finished(self, success, msg, dst_path):
        self.pd.close()
        if not success:
            QMessageBox.critical(self, "Error", f"Failed to process video:\n{msg}")
            return

        values = (
            self.projectName.text().strip(),
            self.projectNo.text().strip(),
            self.logId.text().strip(),
            self.batteryNo.text().strip(),
            self.operatorName.text().strip(),
            self.dtEdit.dateTime().toString("yyyy-MM-dd HH:mm:ss"),
            self.remarks.toPlainText().strip(),
            str(dst_path), None, datetime.datetime.now().isoformat(timespec='seconds')
        )
        execute("""
            INSERT INTO recordings (project_name, project_no, log_id, battery_no, operator_name,
                                    datetime, remarks, video_path, duration_ms, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, values)

        if self.on_saved: self.on_saved()
        self._clear()
        QMessageBox.information(self, "Saved", "Recording saved successfully.")
