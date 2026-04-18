import subprocess
import time
import json
import os
import sys
import glob

# --- CONFIG ---
REMOTE = "mypikpak"
REMOTE_PATH = "/Download/temp/"
LOCAL_DIR = "./assets/download/"
CLEAN_PATHS = ["./assets/download/", "./assets/audio/", "./assets/image/", "./assets/trim_audio/"]

def run_cmd(args):
    return subprocess.run(args, capture_output=True, text=True)

def download():
    # 1. Load Metadata
    if not os.path.exists("metadata.json"):
        print("❌ Error: metadata.json not found.")
        sys.exit(1)
        
    with open("metadata.json", "r") as f:
        meta = json.load(f)
    
    VIDEO_URL = meta['yt_url']
    VIDEO_ID = meta['video_id']
    PREFETCH_LIST = meta.get('prefetch_urls', [])

    # 2. Cleanup local folders
    print("🧹 Cleaning local asset folders...")
    for folder in CLEAN_PATHS:
        os.makedirs(folder, exist_ok=True)
        for f in glob.glob(os.path.join(folder, "*")):
            try: os.remove(f)
            except: pass

    # --- STEP 3 & 4: SMART CLOUD DISPATCH ---
    print(f"📡 Scanning Cloud storage for existing files...")
    # Get a list of everything currently in the temp folder
    cloud_files = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"]).stdout
    
    # 1. Handle Pre-fetch URLs (Warm-up)
    if PREFETCH_LIST:
        for url in PREFETCH_LIST:
            # Extract Video ID from URL to check if we already have it
            p_vid_id = url.split("v=")[-1]
            if p_vid_id in cloud_files:
                print(f"  > Skip Warm-up: {p_vid_id} already in Cloud.")
            else:
                run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", url])
                print(f"  > Warm-up dispatched: {url}")

    # 2. Handle Active Video
    file_name = None
    for line in cloud_files.splitlines():
        if VIDEO_ID in line:
            file_name = line
            print(f"⏩ Instant Hit! {file_name} found in Cloud.")
            break

    if not file_name:
        print(f"🆕 Active Video {VIDEO_ID} not found. Sending to PikPak...")
        send_res = run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", VIDEO_URL])
        try:
            task_data = json.loads(send_res.stdout)
            file_name = task_data.get("file_name")
        except:
            # If PikPak returns an error because the task is already active
            # we try to find the filename again in a second
            print("⚠️ PikPak task might already be active. Re-scanning...")
            time.sleep(2)
            new_check = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
            for line in new_check.stdout.splitlines():
                if VIDEO_ID in line:
                    file_name = line
                    break
            
            if not file_name:
                print("❌ Failed to secure a filename for this task.")
                sys.exit(1)

    # --- STEP 5 - POLLING LOOP ---
    print(f"⏳ Waiting for Cloud Muxing...")
    spinner = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    
    for i in range(120):
        symbol = spinner[i % len(spinner)]
        list_cmd = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
        
        if file_name in list_cmd.stdout:
            # Verify file is finished (Size > 1KB)
            size_cmd = run_cmd(["rclone", "lsjson", f"{REMOTE}:{REMOTE_PATH}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                if size_data.get("Size", 0) > 1000:
                    print(f"\n✨ FILE READY! Size: {size_data['Size']/1024/1024:.2f} MB")
                    break
            except: pass
            print(f"\r{symbol} [{i*5}s] File detected, stitching...", end="")
        else:
            print(f"\r{symbol} [{i*5}s] PikPak is fetching...", end="")
        
        sys.stdout.flush()
        time.sleep(5)
    else:
        print("\n⏰ Timeout.")
        sys.exit(1)

    # --- STEP 6 - PULL TO RUNNER ---
    dest_path = os.path.join(LOCAL_DIR, file_name)
    print(f"🚀 Pulling to GitHub Runner...")
    run_cmd(["rclone", "copyto", f"{REMOTE}:{REMOTE_PATH}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        print(f"🏆 Downloaded: {dest_path}")
    else:
        sys.exit(1)

if __name__ == "__main__":
    download()
