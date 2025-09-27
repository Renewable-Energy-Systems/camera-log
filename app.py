# app.py
import sys
from PySide6.QtWidgets import QApplication
from core.db import init_db
from core.paths import APP_DIR
from core.style import apply_style
from main_window import MainWindow

def main():
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("RES – Stack Assembly Dashboard")
    apply_style(app)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
