import os
import json
import subprocess

def sync_cleanup():
    if not os.path.exists("metadata.json"):
        print("❌ Metadata missing, cleanup skipped.")
        return

    with open("metadata.json", "r") as f:
        meta = json.load(f)

    # 1. Identify what we MUST KEEP
    # We keep the one we just pre-fetched for the NEXT run
    prefetch_list = meta.get('prefetch_urls', [])
    keep_ids = []
    for url in prefetch_list:
        keep_ids.append(url.split("v=")[-1].split("&")[0])

    remote_path = "/Download/temp/"
    remote_name = "mypikpak"

    print(f"📡 Scanning Cloud for unnecessary files...")
    
    # 2. List all files currently in the cloud
    ls_cmd = ["rclone", "lsf", f"{remote_name}:{remote_path}"]
    res = subprocess.run(ls_cmd, capture_output=True, text=True)
    cloud_files = res.stdout.splitlines()

    # 3. Delete anything that doesn't match our 'Keep' list
    for file_name in cloud_files:
        should_keep = False
        for vid_id in keep_ids:
            if vid_id in file_name:
                should_keep = True
                break
        
        if not should_keep:
            print(f"🗑️ Purging abandoned/old file: {file_name}")
            del_cmd = ["rclone", "delete", f"{remote_name}:{remote_path}{file_name}"]
            subprocess.run(del_cmd)
        else:
            print(f"✅ Keeping pre-fetch file for next run: {file_name}")

if __name__ == "__main__":
    sync_cleanup()
