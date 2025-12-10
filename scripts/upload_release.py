import os
import sys
import requests
from pathlib import Path

# Config
GITHUB_REPO = "Renewable-Energy-Systems/camera-log"
TAG_NAME = "v1"
FILE_PATH = Path(r"d:\projects\camlog\Output\RES_Stack_Recorder_Setup.exe")
ASSET_NAME = "RES_Stack_Recorder_Setup.exe"

import webbrowser

def get_token():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("Error: GITHUB_TOKEN environment variable not set.")
        print("Opening GitHub settings page...")
        webbrowser.open("https://github.com/settings/tokens/new?scopes=repo&description=CamLog+Release+Upload")
        print("Please generate a 'classic' token with 'repo' scope.")
        print("Then run: $env:GITHUB_TOKEN='your_token'; python scripts/upload_release.py")
        sys.exit(1)
    return token

def upload_asset():
    token = get_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get Release ID for tag
    print(f"Fetching release for tag: {TAG_NAME}...")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{TAG_NAME}"
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        print(f"Error fetching release: {r.status_code} {r.text}")
        sys.exit(1)
    
    release = r.json()
    upload_url = release["upload_url"].split("{")[0] # clean template
    assets = release.get("assets", [])
    
    # 2. Delete existing asset if present
    for asset in assets:
        if asset["name"] == ASSET_NAME:
            print(f"Deleting existing asset {ASSET_NAME} (id: {asset['id']})...")
            del_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/assets/{asset['id']}"
            requests.delete(del_url, headers=headers)
            break

    # 3. Upload new asset
    if not FILE_PATH.exists():
        print(f"Error: File not found at {FILE_PATH}")
        print("Did you compile the installer script?")
        sys.exit(1)

    print(f"Uploading {FILE_PATH}...")
    with open(FILE_PATH, 'rb') as f:
        data = f.read()
        
    params = {"name": ASSET_NAME}
    headers["Content-Type"] = "application/octet-stream"
    
    r = requests.post(upload_url, headers=headers, params=params, data=data)
    if r.status_code in (201, 200):
        print("Success! Asset uploaded.")
        print(f"Download link: {r.json().get('browser_download_url')}")
    else:
        print(f"Upload failed: {r.status_code} {r.text}")

if __name__ == "__main__":
    upload_asset()
