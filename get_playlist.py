import os
import json
from ytmusicapi import YTMusic, OAuthCredentials

def get_ytm_client():
    oauth_raw = os.environ.get("YTM_OAUTH_JSON")
    auth_keys = OAuthCredentials(
        client_id=os.environ.get("YTM_CLIENT_ID"),
        client_secret=os.environ.get("YTM_CLIENT_SECRET")
    )
    with open("oauth.json", "w") as f:
        f.write(oauth_raw)
    return YTMusic("oauth.json", oauth_credentials=auth_keys)

def main():
    yt = get_ytm_client()
    playlist_id = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

    # TEST 1: Basic Connectivity
    try:
        user = yt.get_account_info()
        print(f"DEBUG 1: OAuth is WORKING. Logged in as: {user.get('name')}")
    except Exception as e:
        print(f"DEBUG 1: OAuth is BROKEN. The token is invalid: {e}")
        return

    # TEST 2: Read Access
    try:
        playlist = yt.get_playlist(playlist_id)
        print(f"DEBUG 2: READ Access is WORKING. Found {len(playlist['tracks'])} tracks.")
    except Exception as e:
        print(f"DEBUG 2: READ Access FAILED. Check if Playlist ID is correct: {e}")
        return

    # TEST 3: Write Access (The Problem Child)
    print("DEBUG 3: Testing WRITE Access (Attempting to remove first item)...")
    if playlist['tracks']:
        try:
            track = playlist['tracks'][0]
            # We try a different method: remove_playlist_items via raw IDs
            res = yt.remove_playlist_items(playlist_id, [track])
            print(f"DEBUG 3: WRITE Access SUCCESS! Response: {res}")
        except Exception as e:
            print(f"DEBUG 3: WRITE Access FAILED: {e}")
            print("REASON: Your token has Read-only permission, but not Write permission.")
