#!/bin/bash
mkdir -p ./assets/audio ./assets/image

# Just find the file. Do NOT delete anything here.
INPUT_FILE=$(ls ./assets/download/* 2>/dev/null | head -n 1)

if [ -z "$INPUT_FILE" ]; then
    echo "❌ No file found in ./assets/download"
    exit 1
fi

echo "🎬 Splitting: $INPUT_FILE"
ffmpeg -y -i "$INPUT_FILE" -vn -ar 44100 -ac 2 -b:a 192k ./assets/audio/audio.mp3
ffmpeg -y -i "$INPUT_FILE" -frames:v 1 -q:v 2 ./assets/image/image.jpg
