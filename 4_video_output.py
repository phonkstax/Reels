#!/usr/bin/env python3
import librosa
import numpy as np
import os
import subprocess
import json
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
import moviepy.video.fx as vfx

# --- CONFIG ---
# These paths match your GitHub/Git structure
AUDIO_PATH = "./assets/audio/audio.mp3"
LOGO_PATH = "./assets/spotify.png"
METADATA_PATH = "metadata.json"
OUT_DIR = "./output/video"

# Temporary files used during the render process
TEMP_VIDEO = "./temp_visual.mp4"
BLUR_BG_PATH = "./temp_blurred_bg.png"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Dynamic Image Selection: Grabs the first image in the folder
IMAGE_DIR = "./assets/image/"
if os.path.exists(IMAGE_DIR) and os.listdir(IMAGE_DIR):
    IMAGE_PATH = os.path.join(IMAGE_DIR, os.listdir(IMAGE_DIR)[0])
else:
    IMAGE_PATH = "./assets/image/image.jpg"

def get_filename():
    """Reads metadata.json to determine the final filename."""
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                data = json.load(f)
                artist = data.get('artist', 'Artist').replace(' ', '_')
                track = data.get('track', 'Track').replace(' ', '_')
                return f"{artist}_-_{track}.mp4"
        except Exception:
            pass
    return "output_reel.mp4"

def prepare_blurred_background():
    """Uses FFmpeg to create a high-quality blurred background fast."""
    print("--- Stage 1: Creating Blurred Background ---")
    cmd = [
        "ffmpeg", "-i", IMAGE_PATH, 
        "-vf", "scale=2000:-1,crop=1920:1080,boxblur=20:5", 
        BLUR_BG_PATH, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def make_phonk_edit():
    filename = get_filename()
    final_output = os.path.join(OUT_DIR, filename)
    
    # Generate the blurred asset
    prepare_blurred_background()
    
    print(f"--- Stage 2: Analyzing Audio Rhythm ---")
    audio = AudioFileClip(AUDIO_PATH)
    y, sr = librosa.load(AUDIO_PATH)
    
    # Beat detection for syncing effects
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=2.5, wait=10)
    peak_times = librosa.frames_to_time(peaks, sr=sr)

    # 1. BACKGROUND LAYER (Blurred & Pumping)
    bg_clip = ImageClip(BLUR_BG_PATH).with_duration(audio.duration)
    def bg_effects(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        if time_since_peak < 0.3:
            intensity = 1.0 - (time_since_peak / 0.3)
            frame *= (1.0 - (0.2 * intensity)) # Dark pulse on beat
        return np.clip(frame, 0, 255).astype('uint8')
    bg_final = bg_clip.transform(bg_effects)

    # 2. FOREGROUND LAYER (900x900 Square with Glitches)
    fg_original = ImageClip(IMAGE_PATH).with_duration(audio.duration).resized(height=900)
    fg_square = fg_original.cropped(x_center=fg_original.w/2, width=900)
    
    def square_fx(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        
        # Apply High-Contrast Phonk Grade
        frame = (frame - 128) * 1.6 + 128
        
        if time_since_peak < 0.20:
            intensity = 1.0 - (time_since_peak / 0.20)
            frame *= (1.0 + (0.5 * intensity)) # Flash
            shift = int(15 * intensity)
            if shift > 0:
                # RGB Chromatic Aberration
                frame[:,:,0] = np.roll(frame[:,:,0], shift, axis=1) 
                frame[:,:,2] = np.roll(frame[:,:,2], -shift, axis=1)
        
        return np.clip(frame, 0, 255).astype('uint8')

    fg_final = fg_square.transform(square_fx)

    # 3. LOGO LAYER (Spotify Logo top-left)
    logo = (ImageClip(LOGO_PATH)
            .resized(width=150)
            .with_start(5)
            .with_duration(5)
            .with_effects([vfx.CrossFadeIn(1.0), vfx.CrossFadeOut(1.0)])
            .with_position((50, 50)))

    # 4. COMPOSITE
    final_composition = CompositeVideoClip([
        bg_final, 
        fg_final.with_position("center"), 
        logo
    ], size=(1920, 1080))

    # 5. RENDER VIDEO (Visuals Only)
    print("--- Stage 3: Rendering Visuals ---")
    final_composition.write_videofile(TEMP_VIDEO, fps=30, codec="libx264", preset="ultrafast", audio=False)

    # 6. FINAL MUX (Optimized for Small Size & YouTube)
    print("--- Stage 4: Final Compression & Audio Mux ---")
    # Using CRF 28 and Slow preset for maximum size efficiency
    cmd = [
        "ffmpeg", "-i", TEMP_VIDEO, "-i", AUDIO_PATH, 
        "-c:v", "libx264", "-crf", "28", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", 
        "-shortest", final_output, "-y"
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup temp files to keep the repo clean
    for f in [TEMP_VIDEO, BLUR_BG_PATH]:
        if os.path.exists(f):
            os.remove(f)
            
    print(f"\n--- SUCCESS: {final_output} ---")

if __name__ == "__main__":
    # Ensure mandatory assets exist before starting
    if os.path.exists(AUDIO_PATH) and os.path.exists(LOGO_PATH):
        make_phonk_edit()
    else:
        print(f"Error: Missing assets. Check {AUDIO_PATH} and {LOGO_PATH}")
