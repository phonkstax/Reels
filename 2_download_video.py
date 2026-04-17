import subprocess
import time
import json
import os
import sys
import glob

REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"

def download():
    if not os.path.exists("metadata.json"): return

    # --- CLEANUP PREVIOUS RUNS ---
    print("🧹 Cleaning local download and assets folders...")
    for folder in [LOCAL_DIR, "./assets/audio/", "./assets/image/"]:
        files = glob.glob(os.path.join(folder, "*"))
        for f in files:
            try: os.remove(f)
            except: pass

    os.makedirs(LOCAL_DIR, exist_ok=True)
    
    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # Trigger PikPak
    cmd = ["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", meta['yt_url']]
    send_res = subprocess.run(cmd, capture_output=True, text=True)
    file_name = json.loads(send_res.stdout).get("file_name")

    # Wait and Copy
    for i in range(60):
        list_cmd = subprocess.run(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"], capture_output=True, text=True)
        if file_name in list_cmd.stdout:
            subprocess.run(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", f"{LOCAL_DIR}{file_name}"])
            print(f"✅ Downloaded: {file_name}")
            return
        time.sleep(10)
    sys.exit(1)

if __name__ == "__main__":
    download()
