# widgets/topbar.py
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QLineEdit
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from core.paths import ASSETS_DIR
from core.style import COLORS

class TopBar(QFrame):
    def __init__(self, title_text: str = "RES • Stack Assembly Dashboard"):
        super().__init__()
        self.setObjectName("Card")
        lay = QHBoxLayout(self); lay.setContentsMargins(16,10,16,10)

        logo = QLabel()
        logo_path = ASSETS_DIR / "res_logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo.setPixmap(pix)
        else:
            logo.setText("RES")

        title = QLabel(title_text)
        title.setStyleSheet(f"font-size:20px; font-weight:800; color:{COLORS['primary']};")

        self.searchEdit = QLineEdit()
        self.searchEdit.setPlaceholderText("Global search… (projects, operators, remarks)")
        self.searchEdit.setClearButtonEnabled(True)
        self.searchEdit.setFixedWidth(420)

        lay.addWidget(logo); lay.addSpacing(8); lay.addWidget(title); lay.addStretch(1)
        lay.addWidget(self.searchEdit)
