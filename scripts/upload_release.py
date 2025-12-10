import os
import sys
import requests
from pathlib import Path

import argparse

# Config
GITHUB_REPO = "Renewable-Energy-Systems/camera-log"
FILE_PATH = Path(r"d:\projects\camlog\Output\RES_Stack_Recorder_Setup.exe")
ASSET_NAME = "RES_Stack_Recorder_Setup.exe"

def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", required=True, help="Release tag (e.g., v1.0.2)")
    return parser.parse_args()

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
    args = get_args()
    tag_name = args.tag
    
    token = get_token()
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    # 1. Get Release ID for tag
    print(f"Fetching release for tag: {tag_name}...")
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/tags/{tag_name}"
    r = requests.get(url, headers=headers)
    
    if r.status_code == 404:
        print(f"Release not found for tag {tag_name}. Creating new release...")
        create_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
        payload = {
            "tag_name": tag_name,
            "name": f"Release {tag_name}",
            "body": f"Automated release for version {tag_name}",
            "draft": False,
            "prerelease": False
        }
        r = requests.post(create_url, headers=headers, json=payload)
        if r.status_code not in (200, 201):
             print(f"Error creating release: {r.status_code} {r.text}")
             sys.exit(1)
        release = r.json()
    elif r.status_code != 200:
        print(f"Error fetching release: {r.status_code} {r.text}")
        sys.exit(1)
    else:
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
