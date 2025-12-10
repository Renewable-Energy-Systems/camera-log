import requests
import webbrowser
from packaging import version
from PySide6.QtCore import QThread, Signal

GITHUB_REPO = "Renewable-Energy-Systems/camera-log"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateChecker(QThread):
    update_available = Signal(str, str) # version, url
    
    def __init__(self, current_version):
        super().__init__()
        self.current_version = current_version

    def run(self):
        try:
            response = requests.get(RELEASES_API, timeout=5)
            if response.status_code == 200:
                data = response.json()
                latest_tag = data.get("tag_name", "").lstrip("v")
                html_url = data.get("html_url", "")
                
                if latest_tag and version.parse(latest_tag) > version.parse(self.current_version):
                    self.update_available.emit(latest_tag, html_url)
        except Exception:
            pass # Fail silently

def open_update_url(url):
    webbrowser.open(url)
