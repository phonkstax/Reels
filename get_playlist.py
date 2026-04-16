import os
import json
from ytmusicapi import YTMusic

def get_ytm_client():
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    
    # Ensure the directory exists (helpful for GitHub Actions)
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    # Initialize WITHOUT extra credentials objects first 
    # to see if the JSON file is enough (standard library behavior)
    try:
        # If you have a Brand Account, you might need: YTMusic("oauth.json", brand_id="12345...")
        # For now, let's try the simplest initialization
        return YTMusic("oauth.json")
    except Exception as e:
        print(f"Initialization Error: {e}")
        return None

def main():
    yt = get_ytm_client()
    if not yt:
        return

    print("Testing connection with get_library_playlists...")
    try:
        # This is a lighter call than get_playlist
        test = yt.get_library_playlists(limit=1)
        print("Auth check: Success!")
    except Exception as e:
        print(f"Auth check failed: {e}")
        # Let's print the headers the library is using (careful: hide tokens)
        print("Check if Client ID/Secret are correctly mapped in your secrets!")

    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    try:
        # Force a small limit to reduce payload size
        playlist = yt.get_playlist(playlist_id, limit=20)
        print(f"Playlist Title: {playlist.get('title')}")
        
        for track in playlist.get('tracks', []):
            print(f"ID: {track['videoId']} | {track['title']}")
            
    except Exception as e:
        print(f"Playlist Error: {e}")

if __name__ == "__main__":
    main()
