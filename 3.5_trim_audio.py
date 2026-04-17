import subprocess
import json
import os
import sys

# --- CONFIG ---
INPUT_AUDIO = "./assets/audio/audio.mp3"
# Explicitly set the output path as requested
OUTPUT_PATH = "./assets/trim_audio/trim_audio.mp3"
CLIP_LEN = 20
STEP = 4  # Scans every 4 seconds for faster processing

def find_best_drop(file):
    # 1. Get total duration to prevent scanning past the end
    probe = subprocess.run([
        "ffprobe", "-v", "-8", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", file
    ], capture_output=True, text=True)
    
    try:
        duration = float(probe.stdout.strip())
    except:
        print("❌ Could not determine audio duration.")
        return 0

    print(f"🔍 Scanning {int(duration)}s audio for the best 20s drop...")
    best_start = 0
    max_volume = -999

    # 2. Energy Detection Loop
    for t in range(0, int(duration - CLIP_LEN), STEP):
        # We analyze a 1s snippet at each interval to identify the 'peak'
        cmd = [
            "ffmpeg", "-ss", str(t), "-t", "1", 
            "-i", file,
            "-af", "highpass=f=40,lowpass=f=200,volumedetect",
            "-f", "null", "-"
        ]
        p = subprocess.run(cmd, capture_output=True, text=True)
        
        for line in p.stderr.split("\n"):
            if "mean_volume" in line:
                try:
                    # Extracts the volume level (e.g., -12.5)
                    score = float(line.split(":")[1].replace(" dB","").strip())
                    if score > max_volume:
                        max_volume = score
                        best_start = t
                except:
                    pass
    return best_start

def main():
    # Ensure input exists
    if not os.path.exists(INPUT_AUDIO):
        print(f"❌ Input missing: {INPUT_AUDIO}")
        sys.exit(1)

    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Calculate best drop
    start_time = find_best_drop(INPUT_AUDIO)
    print(f"🔥 Best drop found at {start_time}s. Extracting 20s clip...")

    # 3. Perform the Trim
    # We use libmp3lame to ensure a clean re-encode of the 20s section
    trim_cmd = [
        "ffmpeg", "-y",
        "-ss", str(start_time),
        "-t", str(CLIP_LEN),
        "-i", INPUT_AUDIO,
        "-acodec", "libmp3lame",
        "-b:a", "192k",
        OUTPUT_PATH
    ]
    
    subprocess.run(trim_cmd)
    
    if os.path.exists(OUTPUT_PATH):
        print(f"✅ Trimmed audio saved to: {OUTPUT_PATH}")
    else:
        print("❌ Error: Trimmed file was not created.")

if __name__ == "__main__":
    main()
