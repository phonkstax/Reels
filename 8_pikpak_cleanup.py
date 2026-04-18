import os
import json
import subprocess
import sys

def direct_cleanup():
    # 1. Load metadata to find the exact filename we used
    if not os.path.exists("metadata.json"):
        print("⚠️ metadata.json not found. Nothing to clean.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # Get the specific filename saved by Step 2
    file_name = meta.get('cloud_file_name')
    remote_name = "mypikpak"
    remote_path = "Download/temp/"

    if not file_name:
        print("⚠️ No cloud_file_name found in metadata. Skip cleanup.")
        return

    print(f"🗑️ Targeting specific file for deletion: {file_name}")
    
    # 2. Use rclone deletefile to remove ONLY this specific file
    # We use Download/temp/ without the leading slash for better compatibility
    cmd = ["rclone", "deletefile", f"{remote_name}:{remote_path}{file_name}"]
    res = subprocess.run(cmd, capture_output=True, text=True)

    if res.returncode == 0:
        print(f"✅ Successfully deleted {file_name} from PikPak.")
    else:
        # If the file is already gone, we don't want to fail the whole workflow
        print(f"ℹ️ Cleanup note: {res.stderr.strip()}")

if __name__ == "__main__":
    direct_cleanup()
