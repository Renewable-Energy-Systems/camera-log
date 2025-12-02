# app.py
import sys
from PySide6.QtWidgets import QApplication, QMessageBox, QFileDialog
from core.db import init_db
from core.paths import APP_DIR
from core.style import apply_style
from main_window import MainWindow
import core.config_manager as config_manager
import core.paths as paths

# Fix for PyInstaller noconsole mode where stdout/stderr are None
class NullWriter:
    def write(self, data): pass
    def flush(self): pass

if sys.stdout is None: sys.stdout = NullWriter()
if sys.stderr is None: sys.stderr = NullWriter()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RES – Stack Assembly Dashboard")
    apply_style(app)

    # 1. Check/Set Data Path
    if not config_manager.get_data_path():
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("Setup")
        msg.setText("Please select a folder to store data (videos, database).")
        msg.exec()
        
        path = QFileDialog.getExistingDirectory(None, "Select Data Folder")
        if path:
            config_manager.set_data_path(path)
        else:
            # Default to AppData if cancelled
            default_path = config_manager.get_app_data_dir() / "data"
            reply = QMessageBox.question(None, "Default Path", 
                f"No path selected. Use default location?\n{default_path}",
                QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                config_manager.set_data_path(default_path)
            else:
                sys.exit(0)

    # 2. Ensure directories
    paths.get_videos_dir().mkdir(parents=True, exist_ok=True)
    paths.get_snap_dir().mkdir(parents=True, exist_ok=True)

    # 3. Init DB
    init_db()

    win = MainWindow()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
