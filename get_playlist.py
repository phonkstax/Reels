import os
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    # Load secrets
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    client_id = os.environ.get("YTM_CLIENT_ID")
    client_secret = os.environ.get("YTM_CLIENT_SECRET")

    # Save to file
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)

    # Initialize OAuth credentials object
    auth = OAuthCredentials(
        client_id=client_id,
        client_secret=client_secret
    )

    # Force initialization with credentials
    return YTMusic("oauth.json", oauth_credentials=auth)

def main():
    yt = get_ytm_client()
    
    # The clean ID from your URL
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"
    
    try:
        # Some private playlists require the 'limit' to be a number 
        # rather than None to avoid server-side sorting issues
        playlist = yt.get_playlist(playlist_id, limit=100)
        
        print(f"--- Playlist Found: {playlist['title']} ---")
        for track in playlist['tracks']:
            print(f"ID: {track['videoId']} | {track['title']}")
            
    except Exception as e:
        print(f"Error details: {e}")

if __name__ == "__main__":
    main()
