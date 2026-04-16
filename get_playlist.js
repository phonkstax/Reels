const YTMusic = require('ytmusicapi').default;
const fs = require('fs');

async function main() {
    // 1. Load your OAuth JSON from the environment variable
    const oauthRaw = process.env.YTM_OAUTH_JSON;
    if (!oauthRaw) {
        console.error("Error: YTM_OAUTH_JSON secret is missing!");
        process.exit(1);
    }

    // 2. Initialize the client
    // We write the file because the library expects a path
    fs.writeFileSync('oauth.json', oauthRaw);
    const ytmusic = new YTMusic('oauth.json');

    const playlistId = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur";
    const targetVideoId = "-oIMyMEvMLI"; // The one you want to remove

    console.log(`Accessing Private Playlist...`);

    try {
        // 3. Fetch Playlist
        const playlist = await ytmusic.getPlaylist(playlistId);
        console.log(`--- SUCCESS! Found: ${playlist.title} ---`);

        // 4. Find and Remove the item
        const trackToRemove = playlist.tracks.find(t => t.videoId === targetVideoId);

        if (trackToRemove) {
            console.log(`Found: ${trackToRemove.title}. Attempting removal...`);
            
            // In JS, we pass the playlistId and the track's setVideoId
            const response = await ytmusic.removePlaylistItems(playlistId, [trackToRemove]);
            console.log("Removal Status:", response);
        } else {
            console.log("Track not found in playlist. It might already be gone.");
        }

    } catch (error) {
        console.error("Operation Failed!");
        console.error("Server Message:", error.message);
        
        if (error.message.includes("400")) {
            console.log("\nSTILL GETTING 400? CHECK THESE:");
            console.log("1. Ensure your Client ID is 'TVs and Limited Input Devices'.");
            console.log("2. Verify you CHECKED THE BOX for 'Manage YouTube' during login.");
        }
    }
}

main();
