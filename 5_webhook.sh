#!/bin/bash

# --- 1. SETUP FILENAMES ---
# Get the first mp4 in output folder
OUT_FILE=$(ls ./output/*.mp4 2>/dev/null | head -n 1)

if [ ! -f "$OUT_FILE" ]; then
    echo "❌ Error: Final video file was not created."
    exit 1
fi

URL_FILENAME=$(basename "$OUT_FILE")
SAFE_NAME="${URL_FILENAME%.*}" # Remove .mp4 for the JSON payload

# --- 2. GITHUB UPLOAD (FORCE PUSH) ---
echo "-----------------------------------------------"
echo "📤 UPLOADING TO GITHUB REPO..."

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

# Detect branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "🌿 Detected branch: $CURRENT_BRANCH"

# Keep the repo clean: delete other files in output, keep ONLY this one
find ./output -type f ! -name "$URL_FILENAME" -delete

# Add the video and the metadata
git add "$OUT_FILE"
git add metadata.json

# Construct the RAW URL
# Format: https://raw.githubusercontent.com/Owner/Repo/branch/path/to/file
RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/output/${URL_FILENAME}"

echo "⚙️ Force pushing to $CURRENT_BRANCH..."
# Use [skip ci] to prevent an infinite loop of workflow runs!
git commit -m "Refresh Reel: $SAFE_NAME [skip ci]" || git commit --amend --no-edit [skip ci]
git push origin "$CURRENT_BRANCH" --force

# --- 3. WEBHOOK CALL WITH RELIABILITY ---
if [ -n "$WEBHOOK_URL" ]; then
    echo "⏳ Waiting 5 seconds for GitHub Raw servers to sync..."
    sleep 5

    echo "📡 Sending Webhook to Apps Script..."
    PAYLOAD=$(cat <<EOF
{
  "fileUrl": "$RAW_URL",
  "fileName": "$URL_FILENAME"
}
EOF
)
    # Note: We send as JSON. Make sure your Apps Script handles JSON payloads!
    RESPONSE=$(curl -L -s -X POST -H "Content-Type: application/json" -d "$PAYLOAD" "$WEBHOOK_URL")
    
    echo "📩 Server Response: $RESPONSE"
    echo -e "\n✨ Process Complete."
fi
echo "-----------------------------------------------"
