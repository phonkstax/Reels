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

    # --- NEW: STEP 3 - PRE-FETCH WARM-UP ---
    if PREFETCH_LIST:
        print(f"⚡ Starting background warm-up for {len(PREFETCH_LIST)} future reels...")
        for url in PREFETCH_LIST:
            # We fire these and forget; we don't wait for them
            run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", url])
            print(f"  > Warm-up dispatched: {url}")

    # --- STEP 4 - CHECK FOR INSTANT HIT OR DISPATCH ACTIVE ---
    print(f"📡 Checking Cloud for active Video ID: {VIDEO_ID}...")
    list_check = run_cmd(["rclone", "lsf", f"{REMOTE}:{REMOTE_PATH}"])
    
    file_name = None
    # Look for a file in PikPak that contains our Video ID
    for line in list_check.stdout.splitlines():
        if VIDEO_ID in line:
            file_name = line
            print(f"⏩ Instant Hit! Found pre-fetched file: {file_name}")
            break

    if not file_name:
        print(f"🆕 Not in cloud yet. Dispatching fresh request for: {VIDEO_URL}")
        send_res = run_cmd(["rclone", "backend", "addurl", f"{REMOTE}:{REMOTE_PATH}", VIDEO_URL])
        try:
            task_data = json.loads(send_res.stdout)
            file_name = task_data.get("file_name")
        except:
            print("❌ PikPak Error during dispatch.")
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
