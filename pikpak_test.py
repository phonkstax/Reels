import subprocess
import os
import sys
import time

# --- CONFIG ---
USER = os.environ.get("PIKPAK_USER")
PASS = os.environ.get("PIKPAK_PASS")
VIDEO_URL = "https://www.youtube.com/watch?v=tdocUW4aKnY" # Example Phonk track
# --------------

def test_bridge():
    # Define a temporary remote for the command
    # Syntax: :backend,user=XXX,pass=YYY:
    remote = f":pikpak,user='{USER}',pass='{PASS}':"

    print(f"📡 Sending URL to PikPak Cloud: {VIDEO_URL}")
    
    # Step 1: Trigger the Offline Download (addurl)
    # We save it into a folder called 'Phonkstax_Test'
    cmd_add = ["rclone", "backend", "addurl", f"{remote}Phonkstax_Test", VIDEO_URL]
    
    res = subprocess.run(cmd_add, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"❌ Failed to trigger PikPak: {res.stderr}")
        return False

    print("✅ PikPak is processing in the cloud. Waiting 30 seconds...")
    time.sleep(30) # Cloud transfers usually take 5-15 seconds

    # Step 2: List the folder to verify the file exists
    print("📂 Checking PikPak folder...")
    cmd_ls = ["rclone", "lsf", f"{remote}Phonkstax_Test"]
    ls_res = subprocess.run(cmd_ls, capture_output=True, text=True)

    if ls_res.stdout.strip():
        print(f"🎉 FOUND FILE(S):\n{ls_res.stdout}")
        return True
    else:
        print("⚠️ Folder is still empty. PikPak might be slow or the link failed.")
        return False

if __name__ == "__main__":
    if not test_bridge(): sys.exit(1)
