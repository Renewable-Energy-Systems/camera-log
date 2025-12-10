from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout, QMessageBox, QSpacerItem, QSizePolicy
from PySide6.QtCore import Qt
from core.settings import APP, ORG, VERSION
from core.updater import UpdateChecker
from core.style import H1, BODY

class SettingsView(QWidget):
    def __init__(self, check_update_callback):
        super().__init__()
        self.check_update_callback = check_update_callback
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Header
        header = QLabel("Settings")
        header.setStyleSheet(H1)
        layout.addWidget(header)

        # About Card
        card = QFrame()
        card.setObjectName("Card")
        cl = QVBoxLayout(card)
        
        title = QLabel(f"{ORG} {APP}")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a1a;")
        
        ver = QLabel(f"Version {VERSION}")
        ver.setStyleSheet("color: #666; font-size: 14px;")
        
        pub = QLabel("Published by Pranay Kiran")
        pub.setStyleSheet("color: #888; font-size: 12px;")

        cl.addWidget(title)
        cl.addWidget(ver)
        cl.addWidget(pub)
        
        # Update Section
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #eee;")
        cl.addWidget(line)
        
        btn_layout = QHBoxLayout()
        self.btnCheck = QPushButton("Check for Updates")
        self.btnCheck.setFixedWidth(150)
        self.btnCheck.clicked.connect(self._check_update)
        
        self.statusLabel = QLabel("")
        self.statusLabel.setStyleSheet("color: #666;")
        
        btn_layout.addWidget(self.btnCheck)
        btn_layout.addWidget(self.statusLabel)
        btn_layout.addStretch()
        
        cl.addLayout(btn_layout)
        
        layout.addWidget(card)
        layout.addStretch()

    def _check_update(self):
        self.btnCheck.setEnabled(False)
        self.statusLabel.setText("Checking...")
        
        # Use a temporary checker for manual check
        self.checker = UpdateChecker(VERSION)
        self.checker.update_available.connect(self._on_update)
        self.checker.no_update.connect(self._on_no_update)
        self.checker.finished.connect(lambda: self.btnCheck.setEnabled(True))
        
        self.checker.start()

    def _on_update(self, version, url):
        self.statusLabel.setText("Update available!")
        self.check_update_callback(version, url)

    def _on_no_update(self):
        self.statusLabel.setText("You are up to date.")
