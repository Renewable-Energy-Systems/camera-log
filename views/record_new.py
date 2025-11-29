# views/record_new.py
import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QLabel, QFormLayout, QLineEdit, QTextEdit,
                               QPushButton, QHBoxLayout, QFileDialog, QDateTimeEdit, QMessageBox, QFrame, QProgressDialog)
from core.db import execute
from core.paths import VIDEOS_DIR
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
        self.setObjectName("Card")
        self.on_saved = on_saved
        v = QVBoxLayout(self); v.setContentsMargins(16,16,16,16)
        title = QLabel("New Recording"); title.setStyleSheet("font-size:16px; font-weight:700;")
        v.addWidget(title)

        self.projectName = QLineEdit()
        self.projectNo = QLineEdit()
        self.logId = QLineEdit()
        self.batteryNo = QLineEdit()
        self.operatorName = QLineEdit()
        self.dtEdit = QDateTimeEdit(datetime.datetime.now()); self.dtEdit.setCalendarPopup(True)
        self.dtEdit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.remarks = QTextEdit(); self.remarks.setFixedHeight(80)
        self.videoPathEdit = QLineEdit(); self.videoPathEdit.setReadOnly(True)
        self.browseBtn = QPushButton("Choose Video"); self.browseBtn.setProperty("class","outlined")
        self.browseBtn.clicked.connect(self._choose_video)

        row = QHBoxLayout(); row.addWidget(self.videoPathEdit, 1); row.addWidget(self.browseBtn)

        form = QFormLayout()
        form.addRow("Project name", self.projectName)
        form.addRow("Project No.", self.projectNo)
        form.addRow("Log ID", self.logId)
        form.addRow("Battery no.", self.batteryNo)
        form.addRow("Operator name", self.operatorName)
        form.addRow("Date & time", self.dtEdit)
        form.addRow("Remarks", self.remarks)
        container = QWidget(); container.setLayout(row)
        form.addRow("Video upload", container)
        v.addLayout(form)

        actions = QHBoxLayout()
        self.saveBtn = QPushButton("Save Entry"); self.saveBtn.setProperty("class","primary")
        self.clearBtn = QPushButton("Clear"); self.clearBtn.setProperty("class","tonal")
        self.saveBtn.clicked.connect(self._save)
        self.clearBtn.clicked.connect(self._clear)
        actions.addWidget(self.saveBtn); actions.addWidget(self.clearBtn); actions.addStretch(1)
        v.addLayout(actions)

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
