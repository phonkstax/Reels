import subprocess
import json

def get_playlist_items(playlist_url):
    # Use yt-dlp to extract playlist metadata as JSON
    # --flat-playlist: only gets the list, doesn't analyze every video (much faster)
    command = [
        "yt-dlp", 
        "--flat-playlist", 
        "--dump-single-json", 
        playlist_url
    ]
    
    print(f"Fetching items from unlisted playlist...")
    result = subprocess.run(command, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return

    data = json.loads(result.stdout)
    
    print(f"\n--- Playlist: {data.get('title')} ---")
    for entry in data.get('entries', []):
        video_id = entry.get('id')
        title = entry.get('title')
        # This gives you exactly what you need for your Reel automation
        print(f"ID: {video_id} | Title: {title}")

if __name__ == "__main__":
    PLAYLIST_URL = "https://music.youtube.com/playlist?list=PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    get_playlist_items(PLAYLIST_URL)
