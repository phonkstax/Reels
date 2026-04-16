import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    client_id = os.environ.get("YTM_CLIENT_ID")
    client_secret = os.environ.get("YTM_CLIENT_SECRET")

    # Write the file for the library
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    auth = OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret
    )

    # Note: If your account has multiple 'Channels', 
    # you might need to specify the brand_id, but usually it's None.
    return YTMusic("oauth.json", oauth_credentials=auth)

def main():
    yt = get_ytm_client()
    
    # Let's try to get the library playlists first to see if auth is valid
    print("Testing connection...")
    try:
        # If this works, your OAuth is 100% fine
        test = yt.get_library_playlists(limit=1)
        print("Auth check: Success!")
    except Exception as e:
        print(f"Auth check failed: {e}")

    # The Playlist ID
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    try:
        # Use a small limit and no related data to simplify the request
        playlist = yt.get_playlist(playlist_id, limit=50)
        
        print(f"Playlist Title: {playlist.get('title', 'Unknown')}")
        
        # Save tracks to a file for your other Reels scripts
        tracks_data = []
        for track in playlist.get('tracks', []):
            info = {
                "id": track['videoId'],
                "title": track['title'],
                "artist": track['artists'][0]['name'] if track['artists'] else "Unknown"
            }
            tracks_data.append(info)
            print(f"Added: {info['artist']} - {info['title']}")

        with open("playlist_items.json", "w") as f:
            json.dump(tracks_data, f, indent=4)
            
    except Exception as e:
        print(f"Error fetching playlist: {e}")

if __name__ == "__main__":
    main()
