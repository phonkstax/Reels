#!/bin/bash

git config --global user.name "github-actions[bot]"
git config --global user.email "github-actions[bot]@users.noreply.github.com"

CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

echo "🌿 Branch: $CURRENT_BRANCH"

# ==================================================
# 🔴 REEL
# ==================================================

REEL_FILE=$(ls ./output/reel/*.mp4 2>/dev/null | head -n 1)

if [ -f "$REEL_FILE" ]; then

    NAME=$(basename "$REEL_FILE")
    SAFE="${NAME%.*}"

    echo "📦 REEL FILE: $REEL_FILE"

    git add -f "$REEL_FILE"
    git add -f metadata.json

    REL_PATH="${REEL_FILE#./}"
    RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/${REL_PATH}"

    echo "🔗 REEL URL: $RAW_URL"

    git commit -m "Reel: $SAFE [skip ci]" || git commit --amend --no-edit
    git push origin "$CURRENT_BRANCH" --force

    if [ -n "$WEBHOOK_REEL" ]; then
        echo "⏳ Sending REEL webhook..."
        sleep 5

        PAYLOAD=$(jq -n \
          --arg url "$RAW_URL" \
          --arg name "$NAME" \
          '{fileUrl: $url, fileName: $name}')

        curl -s -L -X POST \
          "$WEBHOOK_REEL" \
          -H "Content-Type: application/json" \
          -d "$PAYLOAD"

        echo "📩 REEL sent"
    fi
fi

# ==================================================
# 🔵 VIDEO
# ==================================================

VIDEO_FILE=$(ls ./output/video/*.mp4 2>/dev/null | head -n 1)

if [ -f "$VIDEO_FILE" ]; then

    NAME=$(basename "$VIDEO_FILE")
    SAFE="${NAME%.*}"

    echo "📦 VIDEO FILE: $VIDEO_FILE"

    git add -f "$VIDEO_FILE"
    git add -f metadata.json

    REL_PATH="${VIDEO_FILE#./}"
    RAW_URL="https://raw.githubusercontent.com/${GITHUB_REPOSITORY}/${CURRENT_BRANCH}/${REL_PATH}"

    echo "🔗 VIDEO URL: $RAW_URL"

    git commit -m "Video: $SAFE [skip ci]" || git commit --amend --no-edit
    git push origin "$CURRENT_BRANCH" --force

    if [ -n "$WEBHOOK_VIDEO" ]; then
        echo "⏳ Sending VIDEO webhook..."
        sleep 5

        PAYLOAD=$(jq -n \
          --arg url "$RAW_URL" \
          --arg name "$NAME" \
          '{fileUrl: $url, fileName: $name}')

        curl -s -L -X POST \
          "$WEBHOOK_VIDEO" \
          -H "Content-Type: application/json" \
          -d "$PAYLOAD"

        echo "📩 VIDEO sent"
    fi
fi

echo "✨ DONE"
