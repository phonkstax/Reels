import os
import requests
import json

# Your Playlist ID
PLAYLIST_ID = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur"

def get_access_token():
    # Uses your stored secrets to get a fresh 1-hour session
    url = "https://oauth2.googleapis.com/token"
    oauth_data = json.loads(os.environ['YTM_OAUTH_JSON'])
    payload = {
        "client_id": os.environ['YTM_CLIENT_ID'],
        "client_secret": os.environ['YTM_CLIENT_SECRET'],
        "refresh_token": oauth_data['refresh_token'],
        "grant_type": "refresh_token"
    }
    r = requests.post(url, data=payload)
    return r.json().get('access_token')

def list_items():
    token = get_access_token()
    # Official Google API endpoint for playlist items
    url = f"https://www.googleapis.com/youtube/v3/playlistItems"
    params = {
        "part": "snippet,contentDetails",
        "playlistId": PLAYLIST_ID,
        "maxResults": 50
    }
    headers = {"Authorization": f"Bearer {token}"}
    
    r = requests.get(url, params=params, headers=headers)
    data = r.json()

    print(f"--- Playlist Items for {PLAYLIST_ID} ---")
    for item in data.get('items', []):
        # THIS IS THE ONE: The real Playlist Item ID for deletion
        playlist_item_id = item['id']
        video_id = item['contentDetails']['videoId']
        title = item['snippet']['title']
        
        print(f"Video ID: {video_id} | Playlist Item ID: {playlist_item_id} | Title: {title}")

if __name__ == "__main__":
    list_items()
