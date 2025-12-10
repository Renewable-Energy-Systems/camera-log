import os
import re
import sys
import subprocess
from pathlib import Path

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
SETTINGS_FILE = PROJECT_DIR / "core" / "settings.py"
INSTALLER_FILE = PROJECT_DIR / "installer.iss"

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
    # Use \g<1> for group reference to avoid ambiguity with numbers
    new_content = re.sub(r'(#define MyAppVersion ")(.*?)(")', f'\\g<1>{new_v}\\g<3>', content)
    INSTALLER_FILE.write_text(new_content, encoding="utf-8")

import argparse

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fast", action="store_true", help="Fast build (low compression)")
    return parser.parse_args()

def main():
    args = get_args()
    
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
    # Clean build only if not fast? Or always? standard is usually fine.
    # We can add --noconfirm.
    run_cmd(["python", "-m", "PyInstaller", "build.spec", "--noconfirm"])
    
    # 3. Compile Installer
    print(f"\n--- Compiling Installer (Inno Setup) {'[FAST MODE]' if args.fast else ''} ---")
    
    iscc_cmd = [str(ISCC_PATH)]
    if args.fast:
        # Use zip and no solid compression for speed
        iscc_cmd.extend(["/DMyCompression=zip", "/DMySolid=no"])
    
    iscc_cmd.append("installer.iss")
    run_cmd(iscc_cmd)
    
    print("\n[SUCCESS] Build process completed!")
    print(f"New Version: {new_v}")
    print(f"Installer available at: Output/RES_Stack_Recorder_Setup.exe")

if __name__ == "__main__":
    main()
