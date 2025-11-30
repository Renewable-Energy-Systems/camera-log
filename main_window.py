# main_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QFrame
from widgets.topbar import TopBar
from views.dashboard import DashboardView
from views.record_new import RecordNewView
from views.record_list import RecordListView

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RES – Stack Assembly Dashboard")
        self.setMinimumSize(1280, 800)

        self.topbar = TopBar()
        self.stack = QStackedWidget()

        # Views
        self.dashboard = DashboardView()
        self.recordNew = RecordNewView(on_saved=self._after_save)
        self.recordList = RecordListView()

        self.stack.addWidget(self.dashboard)   # 0
        self.stack.addWidget(self.recordNew)   # 1
        self.stack.addWidget(self.recordList)  # 2

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
        
        # Set initial state
        self.btnDashboard.setChecked(True)

        rl.addWidget(self.btnDashboard)
        rl.addWidget(self.btnNew)
        rl.addWidget(self.btnList)
        rl.addStretch(1)

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

    def _switch(self, idx: int):
        self.stack.setCurrentIndex(idx)
        
        # Update nav buttons state
        self.btnDashboard.setChecked(idx == 0)
        self.btnNew.setChecked(idx == 1)
        self.btnList.setChecked(idx == 2)

        if idx == 0:
            self.stack.removeWidget(self.dashboard)
            self.dashboard = DashboardView()
            self.stack.insertWidget(0, self.dashboard)
            self.stack.setCurrentIndex(0)
        elif idx == 2:
            self.recordList.refresh()

    def _after_save(self):
        self._switch(2)

    def _global_search(self, text: str):
        self._switch(2)
        self.recordList.refresh(text)
