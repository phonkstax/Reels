#!/bin/bash
mkdir -p ./assets/audio ./assets/image

# Use quotes and a safer way to handle filenames with spaces
INPUT_FILE=$(find ./assets/download -type f | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "❌ No file found in ./assets/download"
    exit 1
fi

echo "🎬 Splitting: $INPUT_FILE"

# Added quotes around "$INPUT_FILE" to handle spaces
ffmpeg -y -i "$INPUT_FILE" -vn -ar 44100 -ac 2 -b:a 192k "./assets/audio/audio.mp3"
ffmpeg -y -i "$INPUT_FILE" -frames:v 1 -q:v 2 "./assets/image/image.jpg"
