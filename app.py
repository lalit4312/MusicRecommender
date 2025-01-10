from flask import Flask, render_template, request, jsonify
import pickle
from youtubesearchpython import VideosSearch
from recommender import hybrid_recommend, get_metadata
from youtubesearchpython.__future__ import VideosSearch
import asyncio

app = Flask(__name__)

# Load data
data = pickle.load(open("pickles/data.pkl", "rb"))


@app.route("/")
def index():
    """Render the main page."""
    tracks = data["track_name"].tolist()
    return render_template("index.html", tracks=tracks)


async def fetch_youtube_data(song):
    """Fetch YouTube video details asynchronously for a given song."""
    search_query = f"{song['track_name']} {song['track_artist']}"
    video_search = VideosSearch(
        search_query, limit=5
    )  # Fetch more results to check alternatives
    result = await video_search.next()

    # Check for embeddable videos
    for video in result.get("result", []):
        # If the video is not live and embeddable, return it
        if not video.get("isLive", False) and video.get("id"):
            return {
                "thumbnail": video.get("thumbnails", [{}])[0].get("url", ""),
                "video_id": video.get("id", ""),
                "watch_url": f"https://www.youtube.com/watch?v={video.get('id')}",
                "embeddable": True,
            }

    # Return fallback data if no embeddable video is found
    return {
        "thumbnail": "",
        "video_id": "",
        "watch_url": f"https://www.youtube.com/results?search_query={search_query.replace(' ', '+')}",
        "embeddable": False,
    }


@app.route("/recommend", methods=["POST"])
async def recommend():
    """Handle AJAX request for song recommendations."""
    selected_song = request.form.get("song", "").strip()
    discovery_mode = request.form.get("discovery_mode", "popular")
    count = int(request.form.get("count", 5))

    # Find the song index
    matches = data[data["track_name"].str.lower() == selected_song.lower()]
    if matches.empty:
        return jsonify({"error": f"No song found with the name '{selected_song}'"}), 404

    selected_index = matches.index[0]
    current_song = get_metadata(selected_index)

    # Get recommendations
    prioritize_popular = discovery_mode == "popular"
    recommendations = hybrid_recommend(
        selected_index, count, prioritisePopular=prioritize_popular
    )

    # Add YouTube video details asynchronously
    tasks = []
    for rec_type, songs in recommendations.items():
        for song in songs:
            tasks.append(fetch_youtube_data(song))

    youtube_data = await asyncio.gather(*tasks)

    # Map YouTube data back to recommendations
    index = 0
    for rec_type, songs in recommendations.items():
        for song in songs:
            song.update(youtube_data[index])
            index += 1

    # Search YouTube for the current song
    current_video = await fetch_youtube_data(current_song)

    return jsonify(
        {
            "current_video": current_video,
            "recommendations": recommendations,
        }
    )


if __name__ == "__main__":
    app.run(debug=True)
