import subprocess
import json

def get_playlist_items(playlist_url):
    # We tell yt-dlp to give us the 'id' (video) AND the 'playlist_id' (internal entry ID)
    command = [
        "yt-dlp", 
        "--flat-playlist", 
        "--dump-single-json", 
        playlist_url
    ]
    
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        return

    data = json.loads(result.stdout)
    
    print(f"--- Playlist: {data.get('title')} ---")
    for entry in data.get('entries', []):
        video_id = entry.get('id')
        # This is the "Secret" ID you need for Make.com or API Deletion
        playlist_item_id = entry.get('playlist_index_id') or entry.get('id')
        title = entry.get('title')
        
        print(f"Video ID: {video_id} | Playlist Item ID: {playlist_item_id} | Title: {title}")

if __name__ == "__main__":
    URL = "https://music.youtube.com/playlist?list=PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    get_playlist_items(URL)
