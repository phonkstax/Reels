import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    # 1. Reconstruct the oauth.json file from Secret
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    if not oauth_raw:
        raise ValueError("YTM_OAUTH_JSON secret is missing!")
    
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    # 2. Setup credentials for automatic refreshing
    auth = OAuthCredentials(
        client_id=os.environ.get("YTM_CLIENT_ID"),
        client_secret=os.environ.get("YTM_CLIENT_SECRET")
    )

    return YTMusic("oauth.json", oauth_credentials=auth)

def main():
    yt = get_ytm_client()
    
    # Replace with your actual Playlist ID 
    # (The string after 'list=' in the URL)
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    playlist = yt.get_playlist(playlist_id, limit=None)
    
    print(f"--- Playlist: {playlist['title']} ---")
    
    for track in playlist['tracks']:
        title = track['title']
        artist = track['artists'][0]['name'] if track['artists'] else "Unknown"
        video_id = track['videoId']
        
        # This format is easy to use for further automation (ffmpeg, etc.)
        print(f"ID: {video_id} | {artist} - {title}")

if __name__ == "__main__":
    main()
