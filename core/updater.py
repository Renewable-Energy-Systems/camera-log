import requests
import webbrowser
from packaging import version
from PySide6.QtCore import QThread, Signal

GITHUB_REPO = "Renewable-Energy-Systems/camera-log"
RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

class UpdateChecker(QThread):
    update_available = Signal(str, str) # version, url
    no_update = Signal()
    
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
                
                assets = data.get("assets", [])
                exe_url = None
                for asset in assets:
                    if asset.get("name", "").endswith(".exe"):
                        exe_url = asset.get("browser_download_url")
                        break
                
                target_url = exe_url or html_url
                
                if latest_tag and version.parse(latest_tag) > version.parse(self.current_version):
                    self.update_available.emit(latest_tag, target_url)
                else:
                    self.no_update.emit()
            else:
                self.no_update.emit() # treating error or invalid response as no update for simplicity
        except Exception:
            self.no_update.emit()

class UpdateDownloader(QThread):
    progress = Signal(int)
    finished = Signal(str) # Path to downloaded file
    error = Signal(str)

    def __init__(self, download_url, save_path):
        super().__init__()
        self.url = download_url
        self.path = save_path
        self._is_running = True

    def run(self):
        try:
            r = requests.get(self.url, stream=True)
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            
            with open(self.path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if not self._is_running: return
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            self.progress.emit(int(downloaded * 100 / total))
            
            self.finished.emit(self.path)
        except Exception as e:
            self.error.emit(str(e))

    def stop(self):
        self._is_running = False

def open_update_url(url):
    webbrowser.open(url)
