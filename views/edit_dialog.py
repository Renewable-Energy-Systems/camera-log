from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QDialogButtonBox,
    QPushButton, QHBoxLayout, QLabel, QFileDialog, QMessageBox, QTextEdit
)
from PySide6.QtCore import Qt
from pathlib import Path
import shutil
import datetime
from models.recording import Recording
from core.db import execute

class EditRecordingDialog(QDialog):
    def __init__(self, parent, recording: Recording):
        super().__init__(parent)
        self.recording = recording
        self.new_video_path = None
        self.setWindowTitle(f"Edit Recording: {recording.battery_code}")
        self.setMinimumWidth(400)
        self.setStyleSheet("background-color: white;")

        layout = QVBoxLayout(self)

        # Form
        form = QFormLayout()
        self.batteryName = QLineEdit(recording.battery_name)
        self.batteryCode = QLineEdit(recording.battery_code)
        self.logId = QLineEdit(recording.log_id)
        self.batteryNo = QLineEdit(recording.battery_no)
        self.operatorName = QLineEdit(recording.operator_name)
        self.remarks = QTextEdit(recording.remarks); self.remarks.setMaximumHeight(60)

        form.addRow("Battery Name:", self.batteryName)
        form.addRow("Battery Code:", self.batteryCode)
        form.addRow("Log ID:", self.logId)
        form.addRow("Battery No.:", self.batteryNo)
        form.addRow("Operator:", self.operatorName)
        form.addRow("Remarks:", self.remarks)
        layout.addLayout(form)

        # Video Re-upload
        v_layout = QHBoxLayout()
        self.lblVideo = QLabel(f"Current: {Path(recording.video_path).name}" if recording.video_path else "No video")
        self.lblVideo.setStyleSheet("color: #666;")
        btnUpload = QPushButton("Re-upload Video")
        btnUpload.setProperty("class", "outlined")
        btnUpload.clicked.connect(self._choose_video)
        v_layout.addWidget(QLabel("Video:"))
        v_layout.addWidget(self.lblVideo, 1)
        v_layout.addWidget(btnUpload)
        layout.addLayout(v_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self._save)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _choose_video(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Video", "", "Video Files (*.mp4 *.avi *.mov *.mkv)")
        if path:
            self.new_video_path = Path(path)
            self.lblVideo.setText(f"New: {self.new_video_path.name}")
            self.lblVideo.setStyleSheet("color: #2e7d32; font-weight: bold;")

    def _save(self):
        # 1. Update DB
        now = datetime.datetime.now().isoformat(timespec='seconds')
        
        # Handle video replacement
        final_video_path = self.recording.video_path
        if self.new_video_path:
            # Copy new video to a stable location or overwrite?
            # Strategy: Copy to same dir as old one, or just update path if it's external.
            # Ideally, we keep it in the app's managed folder if possible, but for now let's just use the path
            # or copy it if we want to be safe. Let's just update the path to the new location for simplicity
            # unless we want to enforce a specific storage structure.
            # User request said "re-upload", implying replacing the content.
            final_video_path = str(self.new_video_path)

        try:
            execute("""
                UPDATE recordings SET
                    battery_name=?, battery_code=?, log_id=?, battery_no=?,
                    operator_name=?, remarks=?, video_path=?, updated_at=?
                WHERE id=?
            """, (
                self.batteryName.text().strip(),
                self.batteryCode.text().strip(),
                self.logId.text().strip(),
                self.batteryNo.text().strip(),
                self.operatorName.text().strip(),
                self.remarks.toPlainText().strip(),
                str(final_video_path),
                now,
                self.recording.id
            ))
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update recording: {e}")
