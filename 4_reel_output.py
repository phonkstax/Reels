#!/usr/bin/env python3
import librosa
import numpy as np
import os
import subprocess
import json
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
import moviepy.video.fx as vfx

# --- CONFIG ---
AUDIO_PATH = "./assets/trim_audio/trim_audio.mp3"
LOGO_PATH = "./assets/spotify.png"
METADATA_PATH = "metadata.json"
OUT_DIR = "./output"

# Temporary files
TEMP_VIDEO = "./temp_visual.mp4"
BLUR_BG_PATH = "./temp_blurred_bg.png"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

# Dynamic Image Selection
IMAGE_DIR = "./assets/image/"
if os.path.exists(IMAGE_DIR) and os.listdir(IMAGE_DIR):
    IMAGE_PATH = os.path.join(IMAGE_DIR, os.listdir(IMAGE_DIR)[0])
else:
    IMAGE_PATH = "./assets/image/image.jpg"

def get_filename():
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, 'r') as f:
                data = json.load(f)
                artist = data.get('artist', 'Artist').replace(' ', '_')
                track = data.get('track', 'Track').replace(' ', '_')
                return f"{artist}_-_{track}.mp4"
        except:
            pass
    return "vertical_reel.mp4"

def prepare_blurred_background():
    print("--- Stage 1: Vertical Background Blur ---")
    # Scale to 1920 height and crop to 1080 width for Vertical 9:16
    cmd = [
        "ffmpeg", "-i", IMAGE_PATH, 
        "-vf", "scale=-1:1920,crop=1080:1920,boxblur=25:5", 
        BLUR_BG_PATH, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def make_phonk_edit():
    filename = get_filename()
    final_output = os.path.join(OUT_DIR, filename)
    prepare_blurred_background()
    
    print(f"--- Stage 2: Processing Vertical {filename} ---")
    audio = AudioFileClip(AUDIO_PATH)
    duration = audio.duration
    
    # Beat Detection
    y, sr = librosa.load(AUDIO_PATH)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=2.5, wait=10)
    peak_times = librosa.frames_to_time(peaks, sr=sr)

    # 1. BACKGROUND (Vertical 1080x1920)
    bg_clip = ImageClip(BLUR_BG_PATH).with_duration(duration)
    def bg_effects(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        if time_since_peak < 0.3:
            intensity = 1.0 - (time_since_peak / 0.3)
            frame *= (1.0 - (0.2 * intensity))
        return np.clip(frame, 0, 255).astype('uint8')
    bg_final = bg_clip.transform(bg_effects)

    # 2. FOREGROUND SQUARE (1000x1000 Square)
    # Resized to nearly fill the width of the vertical screen
    fg_original = ImageClip(IMAGE_PATH).with_duration(duration).resized(width=1000)
    fg_square = fg_original.cropped(y_center=fg_original.h/2, height=1000)
    
    def square_fx(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        frame = (frame - 128) * 1.6 + 128
        if time_since_peak < 0.20:
            intensity = 1.0 - (time_since_peak / 0.20)
            frame *= (1.0 + (0.5 * intensity))
            shift = int(18 * intensity)
            if shift > 0:
                frame[:,:,0] = np.roll(frame[:,:,0], shift, axis=1)
                frame[:,:,2] = np.roll(frame[:,:,2], -shift, axis=1)
        return np.clip(frame, 0, 255).astype('uint8')
    fg_final = fg_square.transform(square_fx)

    # 3. LOGO (Dynamic Timing & Bottom Center)
    # Start at duration / 2, stay until the end
    logo_start = duration / 2
    logo_duration = duration - logo_start
    
    logo = (ImageClip(LOGO_PATH)
            .resized(width=200) # Slightly larger for vertical
            .with_start(logo_start)
            .with_duration(logo_duration)
            .with_effects([vfx.CrossFadeIn(0.5)])
            .with_position(("center", 1600))) # 1600px down on a 1920px screen

    # 4. COMPOSITE (Vertical Size)
    final_composition = CompositeVideoClip([
        bg_final, 
        fg_final.with_position(("center", "center")), 
        logo
    ], size=(1080, 1920))

    # 5. RENDER
    print("--- Stage 3: Rendering Vertical Visuals ---")
    final_composition.write_videofile(TEMP_VIDEO, fps=30, codec="libx264", preset="ultrafast", audio=False)

    # 6. FINAL MUX (Optimized for Reels/YouTube Shorts)
    print("--- Stage 4: Final Compression ---")
    cmd = [
        "ffmpeg", "-i", TEMP_VIDEO, "-i", AUDIO_PATH, 
        "-c:v", "libx264", "-crf", "28", "-preset", "slow",
        "-pix_fmt", "yuv420p", "-movflags", "+faststart",
        "-c:a", "aac", "-b:a", "128k", 
        "-shortest", final_output, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup
    for f in [TEMP_VIDEO, BLUR_BG_PATH]:
        if os.path.exists(f): os.remove(f)
    print(f"DONE: {final_output}")

if __name__ == "__main__":
    make_phonk_edit()
