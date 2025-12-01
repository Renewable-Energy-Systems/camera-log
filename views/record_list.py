# views/record_list.py
from pathlib import Path
from PySide6.QtCore import (
    Qt, QAbstractTableModel, QModelIndex, QSortFilterProxyModel, QUrl, QSize,
    QTimer, QEvent, Signal, QThread
)
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, QComboBox, QLineEdit,
    QFrame, QPushButton, QStyle, QMessageBox, QSlider, QSizePolicy, QScrollArea,
    QFileDialog, QGraphicsOpacityEffect, QProgressDialog
)
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtGui import QKeySequence, QAction
import threading

from core.db import query
from core.settings import get_snapshot_dir, set_snapshot_dir
from models.recording import Recording
from models.recording import Recording
from services.media import snapshot_filename
from services.video_processor import process_and_save_video




# ---------------- Table model ----------------
class RecordingTableModel(QAbstractTableModel):
    HEADERS = ["ID","Battery Name","Battery Code","Log ID","Battery No.","Operator","Date/Time","Remarks","Video","Duration (s)"]
    def __init__(self): super().__init__(); self.rows:list[Recording]=[]; self.refresh()
    def refresh(self, text: str = ""):
        self.beginResetModel(); self.rows.clear()
        if text:
            t=f"%{text.lower()}%"
            rows = query("""
                SELECT id,battery_name,battery_code,log_id,battery_no,operator_name,
                       datetime,remarks,video_path,duration_ms,created_at
                FROM recordings
                WHERE lower(battery_name) LIKE ? OR lower(battery_code) LIKE ?
                   OR lower(log_id) LIKE ? OR lower(battery_no) LIKE ?
                   OR lower(operator_name) LIKE ? OR lower(remarks) LIKE ?
                ORDER BY datetime(created_at) DESC
            """, (t,t,t,t,t,t))
        else:
            rows = query("""
                SELECT id,battery_name,battery_code,log_id,battery_no,operator_name,
                       datetime,remarks,video_path,duration_ms,created_at
                FROM recordings ORDER BY datetime(created_at) DESC
            """)
        for r in rows: self.rows.append(Recording(*r))
        self.endResetModel()
    def rowCount(self, parent=QModelIndex()): return len(self.rows)
    def columnCount(self, parent=QModelIndex()): return len(self.HEADERS)
    def data(self, idx, role=Qt.DisplayRole):
        if not idx.isValid(): return None
        r=self.rows[idx.row()]; c=idx.column()
        if role in (Qt.DisplayRole, Qt.EditRole):
            m=[r.id,r.battery_name,r.battery_code,r.log_id,r.battery_no,r.operator_name,
               r.datetime,r.remarks,Path(r.video_path).name if r.video_path else "",
               f"{(r.duration_ms or 0)/1000:.1f}"]
            return m[c]
        return None
    def headerData(self, s, o, role=Qt.DisplayRole):
        if o==Qt.Horizontal and role==Qt.DisplayRole: return self.HEADERS[s]
        return super().headerData(s,o,role)
    def recording_at(self,row:int)->Recording|None: return self.rows[row] if 0<=row<len(self.rows) else None


# ---------------- Fullscreen overlay window ----------------
class FullscreenWindow(QFrame):
    """Borderless top-level with overlay controls that auto-hide; calls on_exit when closing."""
    HIDE_MS = 2000

    def __init__(self, player: QMediaPlayer, back_to: QVideoWidget, on_exit):
        super().__init__(None, Qt.Window | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.player = player
        self.back_to = back_to
        self.on_exit = on_exit

        lay = QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.setSpacing(0)
        self.video = QVideoWidget(); lay.addWidget(self.video, 1)
        self.player.setVideoOutput(self.video)

        # Info Overlay - removed from here, moved to __init__ to be sibling

        # Transparent overlay
        self.overlay = QFrame(self)
        self.overlay.setStyleSheet("background: rgba(0,0,0,0.35);")
        self.overlay.setVisible(False)
        self.overlay.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self._ov_eff = QGraphicsOpacityEffect(self.overlay)
        self.overlay.setGraphicsEffect(self._ov_eff)

        ov = QVBoxLayout(self.overlay); ov.setContentsMargins(16,16,16,16); ov.setSpacing(8)
        top = QHBoxLayout(); top.addStretch(1)
        self.btnExit = QPushButton("Exit  (Esc)"); self.btnExit.setProperty("class","outlined"); self.btnExit.clicked.connect(self.close)
        top.addWidget(self.btnExit); ov.addLayout(top)

        center = QHBoxLayout(); center.addStretch(1)
        self.btnBig = QPushButton(); self.btnBig.setFixedSize(QSize(80,80)); self.btnBig.setProperty("class","tonal")
        self.btnBig.clicked.connect(self._toggle); center.addWidget(self.btnBig); center.addStretch(1); ov.addLayout(center, 1)

        bottom = QHBoxLayout()
        self.tLeft = QLabel("00:00"); self.tLeft.setStyleSheet("color:white; font-weight:700;")
        self.seek = QSlider(Qt.Horizontal); self.seek.setRange(0,0)
        self.tRight = QLabel("00:00"); self.tRight.setStyleSheet("color:white; font-weight:700;")
        bottom.addWidget(self.tLeft); bottom.addWidget(self.seek,1); bottom.addWidget(self.tRight)
        ov.addLayout(bottom)

        # Wire
        self.seek.sliderMoved.connect(lambda v: self.player.setPosition(v))
        self.seek.sliderReleased.connect(lambda: self.player.setPosition(self.seek.value()))
        self.player.durationChanged.connect(self._on_duration)
        self.player.positionChanged.connect(self._on_pos)
        self.player.playbackStateChanged.connect(self._sync_icon)

        # Auto-hide
        self._hide_timer = QTimer(self); self._hide_timer.setInterval(self.HIDE_MS); self._hide_timer.timeout.connect(self._hide_overlay)
        self.installEventFilter(self); self.setMouseTracking(True)
        
        # Info Overlay - handled by layout

    def resizeEvent(self, e): self.overlay.resize(self.size()); super().resizeEvent(e)
    def showEvent(self, e): super().showEvent(e); self.player.play(); self._reveal_overlay()
    def keyPressEvent(self, e):
        if e.key() in (Qt.Key_Escape, Qt.Key_F11): self.close()
        elif e.key()==Qt.Key_Space: self._toggle()
        else: super().keyPressEvent(e)
    def closeEvent(self, e):
        try:
            self.player.setVideoOutput(self.back_to)
            if callable(self.on_exit): self.on_exit()
        finally:
            super().closeEvent(e)

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress):
            self._reveal_overlay()
            if event.type()==QEvent.MouseButtonPress:
                if not self.overlay.geometry().contains(event.position().toPoint()):
                    self._toggle()
        return super().eventFilter(obj, event)

    # Overlay helpers
    def _reveal_overlay(self):
        self.overlay.setVisible(True); self._ov_eff.setOpacity(1.0); self._hide_timer.start()
    def _hide_overlay(self):
        self._hide_timer.stop(); self._ov_eff.setOpacity(0.0); self.overlay.setVisible(False)

    # Transport/time
    def _toggle(self):
        if self.player.playbackState()==QMediaPlayer.PlayingState: self.player.pause()
        else: self.player.play()
    def _sync_icon(self, st):
        icon = QStyle.SP_MediaPause if st==QMediaPlayer.PlayingState else QStyle.SP_MediaPlay
        self.btnBig.setIcon(self.style().standardIcon(icon))
    def _fmt(self, ms:int):
        s=max(0,ms)//1000; m,s=divmod(s,60); h,m=divmod(m,60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"
    def _on_duration(self, ms:int):
        self.seek.setRange(0, ms if ms>0 else 0); self.tRight.setText(self._fmt(ms))
    def _on_pos(self, ms:int):
        if not self.seek.isSliderDown(): self.seek.setValue(ms); self.tLeft.setText(self._fmt(ms))


# ---------------- Recordings view ----------------
class RecordListView(QFrame):
    def __init__(self):
        super().__init__(); self.setObjectName("Card")
        outer = QVBoxLayout(self); outer.setContentsMargins(12,12,12,12); outer.setSpacing(0)

        scroll = QScrollArea(); scroll.setWidgetResizable(True); outer.addWidget(scroll)
        content = QWidget(); v = QVBoxLayout(content); v.setContentsMargins(0,0,0,0); v.setSpacing(12); scroll.setWidget(content)

        # Filters
        top = QHBoxLayout()
        top.addWidget(QLabel("Quick Filter:"))
        self.field = QComboBox(); self.field.addItems(["All","Battery Name","Battery Code","Log ID","Battery no.","Operator"])
        self.filterEdit = QLineEdit(); self.filterEdit.setPlaceholderText("Type to filter…"); self.filterEdit.setClearButtonEnabled(True)
        top.addWidget(self.field); top.addWidget(self.filterEdit,1); v.addLayout(top)

        # Table
        self.model = RecordingTableModel()
        self.proxy = QSortFilterProxyModel(); self.proxy.setSourceModel(self.model)
        self.proxy.setFilterCaseSensitivity(Qt.CaseInsensitive); self.proxy.setFilterKeyColumn(-1)
        self.table = QTableView(); self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True); self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setSelectionMode(QTableView.SingleSelection)
        self.table.verticalHeader().setVisible(False); self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setMinimumHeight(220); v.addWidget(self.table)

        # Embedded player
        playerCard = QFrame(); playerCard.setObjectName("Card")
        pv = QVBoxLayout(playerCard); pv.setContentsMargins(12,12,12,12); pv.setSpacing(8)
        self.videoWidget = QVideoWidget(); self.videoWidget.setMinimumHeight(320); self.videoWidget.setMaximumHeight(480)
        pv.addWidget(self.videoWidget)

        row = QHBoxLayout()
        self.btnToggle = QPushButton(); self.btnToggle.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.btnToggle.setFixedSize(QSize(40,34)); self.btnToggle.setProperty("class","tonal")
        self.btnStop = QPushButton(self.style().standardIcon(QStyle.SP_MediaStop), ""); self.btnStop.setFixedSize(QSize(36,32)); self.btnStop.setProperty("class","tonal")
        self.seek = QSlider(Qt.Horizontal); self.seek.setRange(0,0)
        self.tLeft = QLabel("00:00"); self.tRight = QLabel("00:00")
        self.btnSnap = QPushButton("Snapshot"); self.btnSnap.setProperty("class","outlined")
        self.btnFull = QPushButton("Fullscreen"); self.btnFull.setProperty("class","outlined")
        self.btnSaveTo = QPushButton("Save To…"); self.btnSaveTo.setProperty("class","outlined")
        self.lblSaveTo = QLabel(str(get_snapshot_dir() or "Default (app/snapshots)")); self.lblSaveTo.setStyleSheet("color:#475569;")
        row.addWidget(self.btnToggle); row.addWidget(self.btnStop); row.addSpacing(8)
        row.addWidget(self.tLeft); row.addWidget(self.seek,1); row.addWidget(self.tRight)
        self.btnSnap = QPushButton("Snapshot"); self.btnSnap.setProperty("class","outlined")
        self.btnDownload = QPushButton("Download"); self.btnDownload.setProperty("class","outlined")
        self.btnFull = QPushButton("Fullscreen"); self.btnFull.setProperty("class","outlined")
        self.btnSaveTo = QPushButton("Save To…"); self.btnSaveTo.setProperty("class","outlined")
        self.lblSaveTo = QLabel(str(get_snapshot_dir() or "Default (app/snapshots)")); self.lblSaveTo.setStyleSheet("color:#475569;")
        row.addWidget(self.btnToggle); row.addWidget(self.btnStop); row.addSpacing(8)
        row.addWidget(self.tLeft); row.addWidget(self.seek,1); row.addWidget(self.tRight)
        row.addStretch(1); row.addWidget(self.btnSnap); row.addWidget(self.btnDownload); row.addWidget(self.btnFull); row.addWidget(self.btnSaveTo); row.addWidget(self.lblSaveTo)
        pv.addLayout(row); v.addWidget(playerCard)

        # Backend
        self.player = QMediaPlayer(); self.audio = QAudioOutput(); self.audio.setVolume(0.8)
        self.player.setAudioOutput(self.audio); self.player.setVideoOutput(self.videoWidget)

        # Wire
        self.filterEdit.textChanged.connect(self._apply_filter)
        self.table.clicked.connect(self._load_current)
        self.table.selectionModel().selectionChanged.connect(self._load_current)
        self.btnToggle.clicked.connect(self._toggle)
        self.player.playbackStateChanged.connect(self._sync_icon)
        self.btnStop.clicked.connect(self.player.stop)
        self.player.durationChanged.connect(self._on_dur)
        self.player.positionChanged.connect(self._on_pos)
        self.seek.sliderMoved.connect(lambda v: self.player.setPosition(v))
        self.seek.sliderReleased.connect(lambda: self.player.setPosition(self.seek.value()))
        self.btnFull.clicked.connect(self._open_fullscreen)
        self.btnSnap.clicked.connect(self._snapshot)
        self.btnDownload.clicked.connect(self._download)
        self.btnSaveTo.clicked.connect(self._choose_snapshot_dir)
        # Double click opens fullscreen (no re-entrancy)
        self.videoWidget.mouseDoubleClickEvent = lambda e: (self._open_fullscreen(), e.accept())

        # Spacebar toggles
        act = QAction(self); act.setShortcut(QKeySequence(Qt.Key_Space)); act.triggered.connect(self._toggle); self.addAction(act)

        # Errors
        if hasattr(self.player, "errorOccurred"):
            self.player.errorOccurred.connect(
                lambda err, msg: QMessageBox.critical(self, "Playback error",
                    f"{msg}\n\nTip: Use MP4 (H.264/AAC) for best compatibility on Windows.")
            )

        self.current_path: Path|None = None
        self.full: FullscreenWindow|None = None

    # ---- filtering
    def _apply_filter(self, text: str):
        mapping={"All":-1,"Battery Name":1,"Battery Code":2,"Log ID":3,"Battery no.":4,"Operator":5}
        self.proxy.setFilterKeyColumn(mapping.get(self.field.currentText(), -1))
        self.proxy.setFilterFixedString(text)

    def refresh(self, search: str = ""):
        self.model.refresh(search); self.table.resizeColumnsToContents()
        self.player.stop(); self.seek.setRange(0,0); self.tLeft.setText("00:00"); self.tRight.setText("00:00")
        self.current_path=None
        self.info_overlay.hide()

    def eventFilter(self, obj, event):
        return super().eventFilter(obj, event)

    # ---- selection
    def _load_current(self, *_):
        idx=self.table.currentIndex()
        if not idx.isValid(): return
        rec=self.model.recording_at(self.proxy.mapToSource(idx).row())
        if not rec or not rec.video_path or not Path(rec.video_path).exists():
            QMessageBox.warning(self,"Missing","Video file not found on disk."); return
        self.current_path=Path(rec.video_path)
        
        self.player.setSource(QUrl.fromLocalFile(str(self.current_path)))
        self.player.play()

    # ---- transport/time
    def _toggle(self):
        if self.player.playbackState()==QMediaPlayer.PlayingState: self.player.pause()
        else: self.player.play()
    def _sync_icon(self, st):
        icon = QStyle.SP_MediaPause if st==QMediaPlayer.PlayingState else QStyle.SP_MediaPlay
        self.btnToggle.setIcon(self.style().standardIcon(icon))
    def _on_dur(self, ms:int):
        self.seek.setRange(0, ms if ms>0 else 0); self.tRight.setText(self._fmt(ms))
    def _on_pos(self, ms:int):
        if not self.seek.isSliderDown(): self.seek.setValue(ms)
        self.tLeft.setText(self._fmt(ms))
    def _fmt(self, ms:int):
        s=max(0,ms)//1000; m,s=divmod(s,60); h,m=divmod(m,60)
        return f"{h:02d}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}"

    # ---- fullscreen
    def _open_fullscreen(self):
        # Already open? do nothing (prevents re-entrancy from double events)
        if self.full is not None: 
            if self.full.isVisible(): 
                return
            else:
                self.full = None
        if not self.current_path: 
            return
        # create and show
        self.full = FullscreenWindow(self.player, self.videoWidget, on_exit=self._on_fullscreen_closed)
        
        # Pass data to fullscreen overlay
        self.full.showFullScreen()

    def _on_fullscreen_closed(self):
        # Called by FullscreenWindow.closeEvent
        self.full = None  # prevent dangling pointer

    # ---- snapshot & folder
    def _snapshot(self):
        if not self.current_path:
            QMessageBox.information(self,"No video","Select and play a recording first."); return
        # Use whichever widget is currently active and valid
        target = self.videoWidget
        if self.full is not None and self.full.isVisible():
            target = self.full.video
        pix = target.grab()
        if pix.isNull():
            QMessageBox.critical(self,"Error","Could not capture frame."); return
        out = snapshot_filename(self.current_path.stem)
        if pix.save(str(out)): QMessageBox.information(self,"Saved",f"Snapshot saved to:\n{out}")
        else: QMessageBox.critical(self,"Error","Failed to save snapshot.")

    def _choose_snapshot_dir(self):
        start = get_snapshot_dir() or Path.home()
        d = QFileDialog.getExistingDirectory(self, "Choose snapshot folder", str(start))
        if d:
            set_snapshot_dir(Path(d))
            self.lblSaveTo.setText(d)

    # ---- download
    def _download(self):
        if not self.current_path:
            QMessageBox.information(self,"No video","Select and play a recording first."); return
        
        idx=self.table.currentIndex()
        if not idx.isValid(): return
        rec=self.model.recording_at(self.proxy.mapToSource(idx).row())
        if not rec: return

        # Ask for save location
        default_name = f"{rec.battery_code}_{rec.battery_no}_overlay.mp4"
        out_path, _ = QFileDialog.getSaveFileName(self, "Save Video", str(Path.home() / default_name), "MP4 Video (*.mp4)")
        if not out_path: return

        # Just copy the file since it already has overlay
        try:
            import shutil
            shutil.copy2(self.current_path, out_path)
            QMessageBox.information(self, "Success", f"Video saved to:\n{out_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save video:\n{e}")
