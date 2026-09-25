#!/bin/bash
set -e

# --- 1. CONFIGURATION ---
TMP=$(mktemp -d)
INPUT_DIR="./reels"
AUDIO_DIR="./audio"
QUOTES_FILE="./assets/quotes.txt"
LOGO_PATH="./assets/spotify.png"
OUTPUT_DIR="./output"

mkdir -p "$OUTPUT_DIR"

# --- 2. ASSET PICKING ---
FILES=($(find "$INPUT_DIR" -maxdepth 1 -type f \( -iname "*.mp4" -o -iname "*.mov" \) | shuf -n 20))
AUDIO_FILE=$(find "$AUDIO_DIR" -maxdepth 1 -type f -iname "*.mp3" | shuf -n 1)

if [ ${#FILES[@]} -eq 0 ]; then
    echo "❌ No videos found"
    exit 1
fi

if [ -z "$AUDIO_FILE" ]; then
    echo "❌ No audio found"
    exit 1
fi

# --- 3. PICK RANDOM QUOTE FOR FILE NAME ONLY ---
TOTAL=$(grep -cve '^[[:space:]]*$' "$QUOTES_FILE")

if [ "$TOTAL" -eq 0 ]; then
    echo "❌ No quotes found"
    exit 1
fi

line=$(shuf -i 1-"$TOTAL" -n 1)
raw=$(sed -n "${line}p" "$QUOTES_FILE" | \
    perl -pe 's/[^[:ascii:]]//g; s/[\x00-\x1f\x7f]//g' | xargs)

# Clean quote for filename
safe_name=$(echo "$raw" | \
    tr -cd '[:alnum:] ' | \
    cut -c1-50 | \
    xargs)

url_filename="${safe_name// /_}.mp4"
out_file="$OUTPUT_DIR/$url_filename"

echo "📝 Selected quote for filename: $raw"
echo "📁 Output file: $url_filename"

# --- 4. MERGE CLIPS ---
echo "🎬 Step 1: Processing Clips..."

i=1

for f in "${FILES[@]}"; do

    ffmpeg -i "$f" -t 1 \
        -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black,fps=30" \
        -c:v libx264 \
        -preset superfast \
        -pix_fmt yuv420p \
        -an \
        "$TMP/clip_$i.mp4" \
        -y -loglevel error

    echo "file '$TMP/clip_$i.mp4'" >> "$TMP/list.txt"

    i=$((i+1))
done

MERGED_RAW="$TMP/merged_raw.mp4"

ffmpeg \
    -f concat \
    -safe 0 \
    -i "$TMP/list.txt" \
    -c copy \
    "$MERGED_RAW" \
    -y -loglevel error

DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$MERGED_RAW")

# --- 5. APPLY LOGO ONLY ---
echo "🎨 Step 2: Applying Spotify Logo (Duration: ${DUR}s)..."

logo_start=$(echo "$DUR" | awk '{print $1 / 2}')
logo_fade_out=$(echo "$DUR" | awk '{print ($1 > 1.5) ? $1 - 1.2 : $1 - 0.2}')

FILTER="[1:v]scale=180:-1,format=rgba,fade=t=in:st=${logo_start}:d=0.5:alpha=1,fade=t=out:st=${logo_fade_out}:d=0.5:alpha=1[logo_p]; \
[0:v][logo_p]overlay=x=(W-w)/2:y=H-h-80:shortest=1[v_f]"

VISUAL_MASTER="$TMP/visual_master.mp4"

ffmpeg \
    -i "$MERGED_RAW" \
    -loop 1 -i "$LOGO_PATH" \
    -filter_complex "$FILTER" \
    -map "[v_f]" \
    -c:v libx264 \
    -preset veryslow \
    -crf 24 \
    -tune stillimage \
    -pix_fmt yuv420p \
    -an \
    "$VISUAL_MASTER" \
    -y -loglevel warning

# --- 6. FINAL AUDIO ---
echo "🎵 Step 3: Adding Audio..."

FADE_VAL=$(echo "$DUR" | awk '{print ($1 > 2) ? $1 - 2 : 0}')

ffmpeg \
    -i "$VISUAL_MASTER" \
    -i "$AUDIO_FILE" \
    -filter_complex "[1:a]afade=t=out:st=${FADE_VAL}:d=2[aud]" \
    -map 0:v \
    -map "[aud]" \
    -c:v copy \
    -c:a aac \
    -b:a 128k \
    -shortest \
    -movflags +faststart \
    "$out_file" \
    -y -loglevel warning

# --- 7. GITHUB UPLOAD ---
if [ -f "$out_file" ]; then

    echo "-----------------------------------------------"
    echo "📤 UPLOADING TO PUBLIC REPO..."

    git config --global user.name "github-actions[bot]"
    git config --global user.email "github-actions[bot]@users.noreply.github.com"

    CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

    echo "🌿 Detected branch: $CURRENT_BRANCH"

    # Cleanup old videos
    find "$OUTPUT_DIR" -type f ! -name "$url_filename" -delete

    git add .
    git add "$out_file"

    RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${url_filename}"

    if [ -n "$GITHUB_ACTIONS" ]; then

        echo "⚙️ Force pushing to $CURRENT_BRANCH..."

        git commit -m "Refresh Reel: $safe_name" || git commit --amend --no-edit

        git push origin "$CURRENT_BRANCH" --force

    fi

    # --- 8. WEBHOOK ---
    if [ -n "$WEBHOOK_URL" ]; then

        echo "📡 Sending Webhook..."

        PAYLOAD=$(cat <<EOF
{
  "fileUrl": "$RAW_URL",
  "fileName": "$safe_name"
}
EOF
)

        curl -L \
            -X POST \
            -H "Content-Type: application/json" \
            -d "$PAYLOAD" \
            "$WEBHOOK_URL"

        echo -e "\n✨ Process Complete."

    fi

    echo "-----------------------------------------------"

else

    echo "❌ Error: Final video file was not created."
    exit 1

fi
