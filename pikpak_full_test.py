import subprocess
import time
import json
import sys
import os

# --- CONFIG ---
REMOTE = "mypikpak"
FOLDER = "/Download/temp/"  # Updated PikPak path
LOCAL_OUTPUT = "./output/"    # Local folder for git testing
VIDEO_URL = "https://www.youtube.com/watch?v=7RvhZyBK9vU"
# --------------

def run_command(args):
    """Utility to run rclone commands and capture output."""
    return subprocess.run(args, capture_output=True, text=True)

def test_round_trip():
    # 0. Prepare Local Output Folder
    if not os.path.exists(LOCAL_OUTPUT):
        os.makedirs(LOCAL_OUTPUT)
        print(f"📁 Created local directory: {LOCAL_OUTPUT}")

    # 1. Trigger the download in PikPak
    print(f"📡 Step 1: Sending URL to PikPak path: {FOLDER}")
    # Ensure remote directory exists
    run_command(["rclone", "mkdir", f"{REMOTE}:{FOLDER}"])
    
    send_cmd = run_command(["rclone", "backend", "addurl", f"{REMOTE}:{FOLDER}", VIDEO_URL])
    
    try:
        task_data = json.loads(send_cmd.stdout)
        file_name = task_data.get("file_name")
        print(f"✅ Task created! Target file: {file_name}")
    except Exception as e:
        print(f"❌ Failed to trigger PikPak. Output: {send_cmd.stdout}")
        return False

    # 2. Polling the Folder (Waiting for file to finish)
    print(f"⏳ Step 2: Watching {FOLDER} for {file_name}...")
    for i in range(60): # 10-minute timeout
        list_cmd = run_command(["rclone", "lsf", f"{REMOTE}:{FOLDER}"])
        
        if file_name in list_cmd.stdout:
            # Check if file has data (is not a 0-byte placeholder)
            size_cmd = run_command(["rclone", "lsjson", f"{REMOTE}:{FOLDER}{file_name}"])
            try:
                size_data = json.loads(size_cmd.stdout)[0]
                if size_data.get("Size", 0) > 1000:
                    print(f"🎉 File ready in cloud! Size: {size_data.get('Size')} bytes.")
                    break
            except:
                pass
        
        if i % 3 == 0:
            print(f"   - [{i*10}s] Still waiting for cloud transfer...")
        time.sleep(10)
    else:
        print("⏰ Timeout: File never appeared in PikPak.")
        return False

    # 3. Pull file to the local ./output/ folder
    dest_path = os.path.join(LOCAL_OUTPUT, file_name)
    print(f"🚀 Step 3: Downloading from cloud to {dest_path}...")
    
    # We use copyto to place the file exactly in our target local folder
    run_command(["rclone", "copyto", f"{REMOTE}:{FOLDER}{file_name}", dest_path])
    
    if os.path.exists(dest_path):
        size = os.path.getsize(dest_path)
        print(f"✅ SUCCESS! File saved to: {dest_path}")
        print(f"📊 Final local size: {size/1024/1024:.2f} MB")
        return True
    else:
        print("❌ Download to local folder failed.")
        return False

if __name__ == "__main__":
    if not test_round_trip(): sys.exit(1)
