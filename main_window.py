# main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame
from PySide6.QtCore import Qt
from widgets.topbar import TopBar
from views.dashboard import DashboardView
from views.record_new import RecordNewView
from views.record_list import RecordListView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stack Assembly Dashboard")
        self.setMinimumSize(1280, 800)

        self.topbar = TopBar()
        self.stack = QStackedWidget()

        # Views
        self.dashboard = DashboardView()
        self.recordNew = RecordNewView(on_saved=self._after_save)
        self.recordList = RecordListView()

        from views.settings import SettingsView # Local import
        self.settingsView = SettingsView(self._show_update_dialog)

        self.stack.addWidget(self.dashboard)   # 0
        self.stack.addWidget(self.recordNew)   # 1
        self.stack.addWidget(self.recordList)  # 2
        self.stack.addWidget(self.settingsView) # 3

        # Left rail
        rail = QFrame(); rail.setObjectName("Card")
        rail.setFixedWidth(250) # Fixed width for rail
        rl = QVBoxLayout(rail); rl.setContentsMargins(12, 20, 12, 20); rl.setSpacing(8)

        def nav_btn(text, icon_name=None, idx=0):
            b = QPushButton(text); b.setObjectName("NavButton")
            b.setCheckable(True)
            b.setAutoExclusive(True)
            b.clicked.connect(lambda: self._switch(idx))
            return b

        self.btnDashboard = nav_btn("Dashboard", idx=0)
        self.btnNew = nav_btn("New Recording", idx=1)
        self.btnList = nav_btn("Recordings", idx=2)
        self.btnSettings = nav_btn("Settings", idx=3)
        
        # Set initial state
        self.btnDashboard.setChecked(True)

        rl.addWidget(self.btnDashboard)
        rl.addWidget(self.btnNew)
        rl.addWidget(self.btnList)
        rl.addStretch(1)
        rl.addWidget(self.btnSettings)

        # Body
        body = QHBoxLayout(); body.setContentsMargins(12,8,12,12); body.setSpacing(12)
        body.addWidget(rail); body.addWidget(self.stack, 1)

        root = QVBoxLayout()
        root.addWidget(self.topbar)
        root.addLayout(body)

        host = QWidget(); host.setLayout(root)
        self.setCentralWidget(host)

        # Global search routes to list
        self.topbar.searchEdit.textChanged.connect(self._global_search)

        # Check for updates
        from core.settings import VERSION
        from core.updater import UpdateChecker, open_update_url
        from PySide6.QtWidgets import QMessageBox

        self.updater = UpdateChecker(VERSION)
        self.updater.update_available.connect(lambda v, url: self._show_update_dialog(v, url))
        self.updater.start()

    def _show_update_dialog(self, version, url):
        from PySide6.QtWidgets import QMessageBox, QProgressDialog
        from PySide6.QtCore import QUrl
        from PySide6.QtGui import QDesktopServices
        from core.updater import open_update_url, UpdateDownloader
        import os
        import subprocess
        import sys
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Update Available")
        msg.setText(f"A new version ({version}) is available!")
        
        is_exe = url.endswith(".exe")
        action_text = "download and install" if is_exe else "download"
        msg.setInformativeText(f"Would you like to {action_text} it now?")
        msg.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        msg.setDefaultButton(QMessageBox.Yes)
        
        if msg.exec() == QMessageBox.Yes:
            if not is_exe:
                open_update_url(url)
                return

            # Start Download
            import tempfile
            temp_dir = tempfile.gettempdir()
            save_path = os.path.join(temp_dir, f"RES_Update_{version}.exe")
            
            self.progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self)
            self.progress.setWindowModality(Qt.WindowModal)
            self.progress.setAutoClose(False)
            self.progress.show()
            
            self.downloader = UpdateDownloader(url, save_path)
            self.downloader.progress.connect(self.progress.setValue)
            self.downloader.error.connect(lambda e: QMessageBox.critical(self, "Error", f"Download failed: {e}"))
            
            def on_finished(path):
                self.progress.close()
                reply = QMessageBox.question(self, "Ready to Install", 
                                           "Download complete. Install now? (The app will close)",
                                           QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    # Launch installer and exit
                    try:
                        subprocess.Popen([path])
                        sys.exit(0)
                    except Exception as e:
                        QMessageBox.critical(self, "Error", f"Failed to launch installer: {e}")

            self.downloader.finished.connect(on_finished)
            self.progress.canceled.connect(self.downloader.stop)
            self.downloader.start()

    def _switch(self, idx: int):
        self.stack.setCurrentIndex(idx)
        
        # Update nav buttons state
        self.btnDashboard.setChecked(idx == 0)
        self.btnNew.setChecked(idx == 1)
        self.btnList.setChecked(idx == 2)
        self.btnSettings.setChecked(idx == 3)

        if idx == 0:
            self.dashboard.refresh()
        elif idx == 2:
            self.recordList.refresh()

    def _after_save(self):
        self._switch(2)

    def _global_search(self, text: str):
        self._switch(2)
        self.recordList.refresh(text)
