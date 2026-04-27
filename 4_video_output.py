#!/usr/bin/env python3
import librosa
import numpy as np
import os
import subprocess
import json
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip
import moviepy.video.fx as vfx

# --- CONFIG ---
AUDIO_PATH = "./assets/audio/audio.mp3"
LOGO_PATH = "./assets/spotify.png"
METADATA_PATH = "metadata.json"
OUT_DIR = "./output"

# Dynamic Image Selection
IMAGE_DIR = "./assets/image/"
if os.path.exists(IMAGE_DIR) and os.listdir(IMAGE_DIR):
    # Grabs the first image file found in the folder
    IMAGE_PATH = os.path.join(IMAGE_DIR, os.listdir(IMAGE_DIR)[0])
else:
    IMAGE_PATH = "./assets/image/image.jpg"

# Temporary files
TEMP_VIDEO = "./temp_visual.mp4"
BLUR_BG_PATH = "./temp_blurred_bg.png"

# Ensure output directory exists
os.makedirs(OUT_DIR, exist_ok=True)

def get_filename():
    """Reads metadata.json to name the file Artist_-_Track.mp4"""
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
    print("--- Stage 1: FFmpeg Background Blur ---")
    # Native FFmpeg blur is much faster than Python
    cmd = [
        "ffmpeg", "-i", IMAGE_PATH, 
        "-vf", "scale=2000:-1,crop=1920:1080,boxblur=20:5", 
        BLUR_BG_PATH, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def make_phonk_edit():
    filename = get_filename()
    final_output = os.path.join(OUT_DIR, filename)
    
    prepare_blurred_background()
    
    print(f"--- Stage 2: Processing {filename} ---")
    audio = AudioFileClip(AUDIO_PATH)
    y, sr = librosa.load(AUDIO_PATH)
    
    # Beat Detection via Librosa
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    peaks = librosa.util.peak_pick(onset_env, pre_max=3, post_max=3, pre_avg=3, post_avg=5, delta=2.5, wait=10)
    peak_times = librosa.frames_to_time(peaks, sr=sr)

    # 1. BACKGROUND LAYER
    bg_clip = ImageClip(BLUR_BG_PATH).with_duration(audio.duration)
    def bg_effects(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        if time_since_peak < 0.3:
            intensity = 1.0 - (time_since_peak / 0.3)
            frame *= (1.0 - (0.2 * intensity)) # Background pulse
        return np.clip(frame, 0, 255).astype('uint8')
    bg_final = bg_clip.transform(bg_effects)

    # 2. FOREGROUND SQUARE LAYER
    fg_original = ImageClip(IMAGE_PATH).with_duration(audio.duration).resized(height=900)
    fg_square = fg_original.cropped(x_center=fg_original.w/2, width=900)
    
    def square_fx(get_frame, t):
        frame = get_frame(t).astype(float)
        diffs = [t - pt for pt in peak_times if t >= pt]
        time_since_peak = min(diffs) if diffs else 999
        
        # Base Phonk Contrast
        frame = (frame - 128) * 1.6 + 128
        
        if time_since_peak < 0.20:
            intensity = 1.0 - (time_since_peak / 0.20)
            frame *= (1.0 + (0.5 * intensity)) # Flash
            shift = int(15 * intensity)
            if shift > 0:
                frame[:,:,0] = np.roll(frame[:,:,0], shift, axis=1) # Red channel shift
                frame[:,:,2] = np.roll(frame[:,:,2], -shift, axis=1) # Blue channel shift
        
        return np.clip(frame, 0, 255).astype('uint8')

    fg_final = fg_square.transform(square_fx)

    # 3. LOGO LAYER (Fades in/out at 5s)
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

    # 5. RENDER VISUALS
    print("--- Stage 3: Rendering Visuals ---")
    final_composition.write_videofile(TEMP_VIDEO, fps=30, codec="libx264", preset="ultrafast", audio=False)

    # 6. FINAL MUX (Compression included for GitHub 100MB limit)
    print("--- Stage 4: Final Muxing ---")
    cmd = [
        "ffmpeg", "-i", TEMP_VIDEO, "-i", AUDIO_PATH, 
        "-c:v", "libx264", "-crf", "26", 
        "-c:a", "aac", "-b:a", "128k", 
        "-shortest", final_output, "-y"
    ]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Cleanup temp files
    for f in [TEMP_VIDEO, BLUR_BG_PATH]:
        if os.path.exists(f):
            os.remove(f)
            
    print(f"--- SUCCESS: {final_output} ---")

if __name__ == "__main__":
    make_phonk_edit()
