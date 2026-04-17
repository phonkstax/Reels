def main():
    token = get_yt_token()
    if not token: sys.exit(1)

    url = "https://www.googleapis.com/youtube/v3/playlistItems"
    params = {"part": "snippet,contentDetails", "playlistId": PLAYLIST_ID, "maxResults": 1}
    r = requests.get(url, params=params, headers={"Authorization": f"Bearer {token}"}).json()
    
    items = r.get('items', [])
    if not items:
        print("❌ Playlist is empty.")
        sys.exit(1)

    item = items[0]
    
    # --- THIS IS THE LINE YOU ARE MISSING ---
    playlist_item_id = item.get('id') 
    
    snippet = item['snippet']
    vid_id = snippet['resourceId']['videoId']
    
    if check_notion_entry(vid_id):
        print(f"⏩ {vid_id} already exists in Notion. Skipping.")
        sys.exit(1)

    raw_artist = snippet.get('videoOwnerChannelTitle', 'Unknown Artist')
    raw_track = snippet.get('title', 'Unknown Track')
    
    artist = clean_name(raw_artist)
    track = clean_name(raw_track)

    # --- ADD IT TO THE DICTIONARY HERE ---
    metadata = {
        "artist": artist,
        "track": track,
        "video_id": vid_id,
        "playlist_item_id": playlist_item_id, 
        "yt_url": f"https://www.youtube.com/watch?v={vid_id}"
    }
    
    with open("metadata.json", "w") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"✅ metadata.json created for: {artist} - {track}")
    print(f"📦 Playlist Item ID: {playlist_item_id}") # This will now show in logs
