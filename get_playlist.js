const YTMusic = require('ytmusic-api').default;
const ytmusic = new YTMusic();

async function main() {
    try {
        // Log in using your Cookie (Save this in a GitHub Secret named YTM_COOKIE)
        // This bypasses the OAuth "400 Bad Request" entirely!
        await ytmusic.initialize(process.env.YTM_COOKIE);

        const playlistId = "PL8WGYt2fhenCJnBHFBKqw8SZl-oyO03Ur";
        
        console.log("Fetching playlist items...");
        const playlist = await ytmusic.getPlaylist(playlistId);
        
        console.log(`Success! Found: ${playlist.name}`);
        
        // Example: List tracks
        playlist.tracks.forEach(track => {
            console.log(`ID: ${track.videoId} | Title: ${track.name}`);
        });

    } catch (error) {
        console.error("Error:", error.message);
    }
}

main();
