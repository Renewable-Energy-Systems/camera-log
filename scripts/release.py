import os
import re
import sys
import subprocess
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_DIR / "core" / "settings.py"
INSTALLER_FILE = PROJECT_DIR / "installer.iss"
UPLOAD_SCRIPT = PROJECT_DIR / "scripts" / "upload_release.py"

# Inno Setup Path - Try standard location
ISCC_PATH = Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe")

def fail(msg):
    print(f"ERROR: {msg}")
    sys.exit(1)

def run_cmd(cmd, cwd=PROJECT_DIR):
    print(f"Running: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd, cwd=str(cwd), shell=True)
    except subprocess.CalledProcessError as e:
        fail(f"Command failed with exit code {e.returncode}")

def get_current_version():
    content = SETTINGS_FILE.read_text(encoding="utf-8")
    m = re.search(r'VERSION\s*=\s*"(\d+\.\d+\.\d+)"', content)
    if not m:
        fail("Could not find VERSION in core/settings.py")
    return m.group(1)

def increment_version(v):
    parts = list(map(int, v.split('.')))
    parts[-1] += 1 # bump patch
    return ".".join(map(str, parts))

def update_settings(new_v):
    print(f"Updating core/settings.py to {new_v}...")
    content = SETTINGS_FILE.read_text(encoding="utf-8")
    new_content = re.sub(r'VERSION\s*=\s*"\d+\.\d+\.\d+"', f'VERSION = "{new_v}"', content)
    SETTINGS_FILE.write_text(new_content, encoding="utf-8")

def update_installer(new_v):
    print(f"Updating installer.iss to {new_v}...")
    content = INSTALLER_FILE.read_text(encoding="utf-8")
    # #define MyAppVersion "1.0.1"
    new_content = re.sub(r'(#define MyAppVersion ")(.*?)(")', f'\\g<1>{new_v}\\g<3>', content)
    INSTALLER_FILE.write_text(new_content, encoding="utf-8")

def main():
    if not ISCC_PATH.exists():
        fail(f"Inno Setup Compiler not found at {ISCC_PATH}. Please install Inno Setup or update script.")

    # 1. Versioning
    cur_v = get_current_version()
    new_v = increment_version(cur_v)
    print(f"Bumping version: {cur_v} -> {new_v}")
    
    update_settings(new_v)
    update_installer(new_v)
    
    # 2. Build App
    print("\n--- Building Executable (PyInstaller) ---")
    run_cmd(["python", "-m", "PyInstaller", "build.spec", "--noconfirm"])
    
    # 3. Compile Installer
    print("\n--- Compiling Installer (Inno Setup) ---")
    run_cmd([str(ISCC_PATH), "installer.iss"])
    
    # 4. Upload
    print(f"\n--- Uploading Release v{new_v} ---")
    # Ensure tag format vX.Y.Z
    tag = f"v{new_v}"
    
    # Check if GITHUB_TOKEN is set
    if "GITHUB_TOKEN" not in os.environ:
        print("WARNING: GITHUB_TOKEN not set. Skipping upload.")
        print(f"To upload manually: python scripts/upload_release.py --tag {tag}")
    else:
        run_cmd(["python", str(UPLOAD_SCRIPT), "--tag", tag])

    print("\n[SUCCESS] Release process completed!")
    print(f"New Version: {new_v}")

if __name__ == "__main__":
    main()
